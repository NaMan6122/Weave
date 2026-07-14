# spec-001-v1 — Auth & User Management (Gaps + Polish)

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-1.1
**TDD Refs:** §8 (Authentication & Security)

---

## 1. Overview

This spec covers the **gaps** in the existing auth system — not a rewrite. The codebase already has:
- NextAuth v5 with Google, GitHub, and Credentials providers (`apps/web/auth.ts`)
- FastAPI JWT auth + API key management (`apps/api/app/routers/auth.py`, `services/auth.py`)
- Middleware protecting `/dashboard/*` routes (`apps/web/middleware.ts`)

**This spec adds:**
- A. OAuth end-to-end plug-in documentation (zero code changes needed)
- B. Email verification flow
- C. Password reset flow
- D. Email service (Resend) with dev-mode console fallback
- E. Database migrations for new tables
- F. Frontend pages for verification and reset flows

---

## 2. OAuth End-to-End Plug-In Guide

### 2.1 Required Environment Variables

```env
# Frontend (.env.local for apps/web)
NEXTAUTH_SECRET=<random-32-char-string>
NEXTAUTH_URL=http://localhost:3000          # or production URL

GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>

GITHUB_CLIENT_ID=<from-github-settings>
GITHUB_CLIENT_SECRET=<from-github-settings>

NEXT_PUBLIC_API_URL=http://localhost:8000    # backend URL
```

### 2.2 OAuth Provider Setup

**Google Cloud Console:**
1. Create OAuth 2.0 Client ID (Web application)
2. Authorized redirect URI: `{NEXTAUTH_URL}/api/auth/callback/google`
3. Authorized JavaScript origin: `{NEXTAUTH_URL}`

**GitHub Developer Settings:**
1. Create OAuth App
2. Authorization callback URL: `{NEXTAUTH_URL}/api/auth/callback/github`

### 2.3 Acceptance Criteria

| # | Criterion | Testable |
|---|-----------|----------|
| AC-2.1 | Google OAuth sign-in creates a user in backend DB and returns a session | Manual: click "Sign in with Google", verify user row in DB |
| AC-2.2 | GitHub OAuth sign-in creates a user in backend DB and returns a session | Manual: click "Sign in with GitHub", verify user row in DB |
| AC-2.3 | Authenticated session persists across page reloads | Manual: reload dashboard, still logged in |
| AC-2.4 | Unauthenticated access to `/dashboard/*` redirects to `/login` | Automated: middleware test |
| AC-2.5 | API key generation works from dashboard after login | Manual: navigate to API Keys page, create key |

---

## 3. Email Verification Flow

### 3.1 Flow

```
Registration (POST /api/v1/auth/register)
  → Create user (email_verified = false)
  → Generate verification token (UUID v4, expires in 24h)
  → Store in email_verifications table
  → Send verification email via Resend
  → Return JWT (user can log in but is unverified)

User clicks link: {FRONTEND_URL}/verify-email?token=xxx
  → Frontend calls GET /api/v1/auth/verify-email?token=xxx
  → Backend validates token (exists, not expired, not used)
  → Sets user.email_verified = true
  → Marks token as used
  → Returns success

Resend verification: POST /api/v1/auth/resend-verification
  → Rate limited: 1 per 5 minutes per user
  → Invalidates previous tokens
  → Sends new email
```

### 3.2 Enforcement

- Unverified users **can** log in and view the dashboard
- Unverified users **cannot** add domains (returns 403 with message)
- Dashboard shows a banner: "Please verify your email to unlock all features"

### 3.3 API Endpoints

**GET `/api/v1/auth/verify-email`**
```
Query: token (string, required)
Response 200: { "message": "Email verified successfully" }
Response 400: { "detail": "Token expired or invalid" }
Response 404: { "detail": "Token not found" }
```

**POST `/api/v1/auth/resend-verification`**
```
Headers: Authorization: Bearer <jwt>
Response 200: { "message": "Verification email sent" }
Response 429: { "detail": "Please wait before requesting another email" }
```

### 3.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Registration sends verification email (or logs to console in dev) |
| AC-3.2 | Clicking valid token marks user as verified |
| AC-3.3 | Expired token (>24h) returns 400 |
| AC-3.4 | Used token returns 400 on second attempt |
| AC-3.5 | Unverified user gets 403 on POST `/api/v1/domains` |
| AC-3.6 | Resend endpoint rate-limits to 1/5min |

---

## 4. Password Reset Flow

### 4.1 Flow

```
POST /api/v1/auth/forgot-password { email }
  → If email exists: generate reset token (UUID v4, expires in 1h)
  → Store in password_resets table
  → Send reset email via Resend
  → Always return 200 (don't leak email existence)

User clicks link: {FRONTEND_URL}/reset-password?token=xxx
  → Frontend shows new password form
  → POST /api/v1/auth/reset-password { token, new_password }
  → Backend validates token (exists, not expired, not used)
  → Hashes new password, updates user
  → Marks token as used
  → Invalidates all existing JWTs (bump a jwt_version counter on user)
  → Returns success
```

### 4.2 API Endpoints

**POST `/api/v1/auth/forgot-password`**
```
Body: { "email": "user@example.com" }
Response 200: { "message": "If that email exists, a reset link has been sent" }
```

**POST `/api/v1/auth/reset-password`**
```
Body: { "token": "uuid", "new_password": "..." }
Response 200: { "message": "Password reset successfully" }
Response 400: { "detail": "Token expired or invalid" }
Response 422: { "detail": "Password must be at least 8 characters" }
```

### 4.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Forgot-password always returns 200 regardless of email existence |
| AC-4.2 | Valid reset token allows password change |
| AC-4.3 | Expired token (>1h) returns 400 |
| AC-4.4 | After reset, old JWT tokens no longer work |
| AC-4.5 | Password minimum 8 characters enforced |
| AC-4.6 | Used token cannot be reused |

---

## 5. Email Service (Resend)

### 5.1 Architecture

```
apps/api/app/services/email.py

class EmailService:
    async send_verification_email(to: str, token: str, user_name: str | None) -> None
    async send_password_reset_email(to: str, token: str, user_name: str | None) -> None
    async send_welcome_email(to: str, user_name: str | None) -> None

class ResendEmailService(EmailService):
    # Uses resend Python SDK
    # Sends from: "Weave <noreply@{WEAVE_EMAIL_DOMAIN}>"

class ConsoleEmailService(EmailService):
    # Logs email content to stdout (for dev/testing)
    # Used when WEAVE_RESEND_API_KEY is empty

def get_email_service() -> EmailService:
    if settings.resend_api_key:
        return ResendEmailService(settings.resend_api_key)
    return ConsoleEmailService()
```

### 5.2 Email Templates

Minimal inline HTML. Each email contains:
- Weave logo/name in header
- Clear action description
- CTA button with link
- Expiry notice
- "If you didn't request this, ignore this email" footer

### 5.3 Configuration

```env
# Backend (.env for apps/api)
WEAVE_RESEND_API_KEY=re_xxxxx     # Leave empty for console mode
WEAVE_EMAIL_DOMAIN=getweave.io    # From domain for emails
WEAVE_FRONTEND_URL=http://localhost:3000  # For building email links
```

### 5.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | With valid Resend key, emails are sent via Resend API |
| AC-5.2 | With empty Resend key, emails are logged to console with full content |
| AC-5.3 | Email contains correct verification/reset link pointing to frontend |
| AC-5.4 | Resend SDK errors are caught and logged (don't crash the registration flow) |

---

## 6. Database Schema Changes

### 6.1 New Tables

```sql
CREATE TABLE email_verifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_email_verif_token ON email_verifications(token);
CREATE INDEX idx_email_verif_user ON email_verifications(user_id);

CREATE TABLE password_resets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pwd_reset_token ON password_resets(token);
CREATE INDEX idx_pwd_reset_user ON password_resets(user_id);
```

### 6.2 User Table Changes

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN password_hash TEXT;  -- if not already present
ALTER TABLE users ADD COLUMN jwt_version INT NOT NULL DEFAULT 0;  -- for invalidation
```

### 6.3 SQLAlchemy Models

New models: `EmailVerification`, `PasswordReset` in `apps/api/app/models/`
Modify: `User` model to add `email_verified`, `password_hash`, `jwt_version` fields.

---

## 7. Frontend Pages

### 7.1 New Routes

| Route | Purpose |
|-------|---------|
| `/verify-email` | Token validation page (calls backend on load) |
| `/forgot-password` | Email input form → calls forgot-password endpoint |
| `/reset-password` | New password form (token from query param) |

### 7.2 Component Behavior

**`/verify-email?token=xxx`**
- On mount: call `GET /api/v1/auth/verify-email?token=xxx`
- Show loading → success message with "Go to Dashboard" link
- On error: show specific message (expired, invalid, already used)

**`/forgot-password`**
- Form: email input + submit button
- On submit: call `POST /api/v1/auth/forgot-password`
- Always show "Check your email" message (don't reveal existence)

**`/reset-password?token=xxx`**
- Form: new password + confirm password
- Validation: min 8 chars, passwords match
- On submit: call `POST /api/v1/auth/reset-password`
- Success: redirect to `/login` with success toast

### 7.3 Dashboard Verification Banner

- If `session.user.emailVerified === false`: show yellow banner at top of dashboard layout
- Banner text: "Please verify your email address. [Resend verification email]"
- Clicking resend calls `POST /api/v1/auth/resend-verification`

---

## 8. Security Considerations

- Verification tokens: single-use, 24h TTL
- Reset tokens: single-use, 1h TTL
- No email existence leakage on forgot-password
- Rate limiting on resend-verification (1/5min per user)
- Rate limiting on forgot-password (3/hour per IP)
- JWT version bump on password reset invalidates all sessions
- Tokens stored as UUID (not guessable)

---

## 9. Dependencies to Add

**Backend (`apps/api/pyproject.toml`):**
```
resend>=2.0
```

**No frontend dependency changes** (existing fetch/API client sufficient).

---

## 10. Out of Scope

- Magic link (passwordless) login — future spec
- MFA/2FA — future spec
- Email change flow — future spec
- Account deletion — future spec
- OAuth account linking (merge GitHub + Google into one user) — future spec
