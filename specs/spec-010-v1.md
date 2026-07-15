# spec-010-v1 — DoDo Payment Integration

**Version:** 1
**Date:** 2026-07-15
**Status:** DRAFT — pending human approval (Gate G1)
**PRD Refs:** §4 (Pricing), FR-7.1 (REST API — billing)
**TDD Refs:** §4.2 (Core API), §5 (Key Algorithms — Credit Calculation), §9 (Deployment — Stripe)
**Depends On:** spec-001-v1 (Auth), spec-003-v1 (Credit System)
**Blocks:** NONE
**Task Reference:** T-005

---

## 1. Overview

Replace Stripe stubs in `apps/api/app/routers/billing.py` and `apps/api/app/config.py` with **DoDo Payments** integration. DoDo is the chosen payment provider (replacing Stripe per product decision). This spec defines the checkout session creation, webhook handling, customer portal access, and plan management for the four pricing tiers (Free, Starter, Pro, Agency).

**Key differences from Stripe:**
- DoDo API endpoints and payload structure differ
- Product/Price IDs will be DoDo-specific
- Webhook event types and signatures differ
- Customer portal URL generation differs

---

## 2. Current State (Stripe Stubs)

**Files to migrate:**
- `apps/api/app/config.py` — `stripe_secret_key`, `stripe_webhook_secret`
- `apps/api/app/routers/billing.py` — `_get_stripe()`, `create_checkout_session()`, `stripe_webhook()`, `list_plans()`
- `apps/api/app/models/user.py` — `stripe_customer_id` column
- Database — `users.stripe_customer_id` column (needs migration to `dodo_customer_id`)

**Current behavior:** All endpoints return 503 if Stripe keys not set. No webhook processing.

---

## 3. DoDo API Mapping (To Be Confirmed from DoDo Docs)

| Stripe Concept | DoDo Equivalent | Notes |
|---|---|---|
| `stripe.checkout.Session.create()` | `POST /v1/checkout/sessions` | DoDo endpoint TBD |
| `price_id` (e.g., `price_...`) | `plan_id` or `product_id` | DoDo uses different ID format |
| `stripe.Webhook.construct_event()` | HMAC verification with `dodo_signature` header | Header name and algorithm TBD |
| `checkout.session.completed` | `checkout.completed` or similar | Event type TBD |
| `customer.subscription.deleted` | `subscription.cancelled` | Event type TBD |
| Stripe Customer Portal | DoDo Billing Portal | URL generation endpoint TBD |
| `stripe.Customer.create()` | `POST /v1/customers` | For linking user to DoDo customer |

**Open Questions (require DoDo docs):**
1. Exact checkout session create endpoint and required parameters
2. Webhook signature header name and verification method
3. Event type names for: successful checkout, subscription cancelled, payment failed
4. Plan/Product ID format (e.g., `plan_starter_monthly` vs `price_...`)
5. Customer portal/billing portal URL generation
6. Test mode vs live mode distinction (sandbox environment?)

---

## 4. Environment Variables

**New (replace Stripe vars in `apps/api/app/config.py`):**

```python
# DoDo Payments
dodo_api_key: str | None = None           # Secret API key (sk_test_... or sk_live_...)
dodo_webhook_secret: str | None = None    # Webhook signing secret (whsec_...)
dodo_base_url: str = "https://api.dodo.is" # Or sandbox URL
```

**Frontend (apps/web/.env.local):**
```env
NEXT_PUBLIC_DODO_PUBLISHABLE_KEY=pk_test_...  # If DoDo uses publishable keys
```

**Plan ID Mapping (backend config):**
```python
DODO_PLAN_IDS = {
    "starter_monthly": "plan_starter_monthly",    # $29/mo
    "pro_monthly": "plan_pro_monthly",            # $79/mo
    "agency_monthly": "plan_agency_monthly",      # $199/mo
    "credits_1000": "plan_credits_1000",          # One-time
    "credits_5000": "plan_credits_5000",          # One-time
}
```

---

## 5. Database Migration

### 5.1 Column Rename
```sql
ALTER TABLE users RENAME COLUMN stripe_customer_id TO dodo_customer_id;
```

### 5.2 SQLAlchemy Model Change
```python
# apps/api/app/models/user.py
dodo_customer_id: Mapped[str | None] = mapped_column(String(255))
```

---

## 6. API Endpoints

### 6.1 POST `/api/v1/billing/checkout`
**Create DoDo Checkout Session**

**Request:**
```json
{
  "plan": "starter_monthly" | "pro_monthly" | "agency_monthly" | "credits_1000" | "credits_5000",
  "domain_id": "uuid" | null
}
```

**Response 200:**
```json
{
  "checkout_url": "https://pay.dodo.is/session/...",
  "session_id": "cs_..."
}
```

**Response 503:** "Payments not configured. Set DODO_API_KEY to enable."
**Response 400:** Invalid plan, domain not owned by user

**Behavior:**
- `mode`: "subscription" for plans, "payment" for credit top-ups
- `success_url`: `{FRONTEND_URL}/dashboard/settings?payment=success`
- `cancel_url`: `{FRONTEND_URL}/dashboard/settings?payment=cancelled`
- `metadata`: `{ user_id, domain_id, plan }`
- For credit top-ups: include `metadata.credit_amount` for webhook fulfillment

### 6.2 POST `/api/v1/billing/webhook`
**Handle DoDo Webhook Events**

**Headers:** `dodo-signature` (or DoDo equivalent)

**Events to Handle:**
| DoDo Event | Action |
|---|---|
| `checkout.completed` (subscription) | Activate user's plan tier; store `dodo_customer_id` on user |
| `checkout.completed` (one-time) | Add credit top-up to user's domain (via `CreditService.add_bonus`) |
| `subscription.cancelled` | Downgrade user to Free tier |
| `subscription.updated` | Handle plan changes (upgrade/downgrade) |
| `payment.failed` | Notify user (webhook `payment.failed`, email via Resend) |

**Response 200:** `{ "received": true }`
**Response 400:** Invalid signature or malformed payload
**Response 503:** DoDo not configured

### 6.3 GET `/api/v1/billing/portal`
**Generate DoDo Billing Portal Session**

**Response 200:**
```json
{ "portal_url": "https://billing.dodo.is/session/..." }
```

**Behavior:** Create portal session for current user's `dodo_customer_id`, return URL for frontend redirect.

### 6.4 GET `/api/v1/billing/plans` (Unchanged)
**Return static plan definitions with DoDo plan IDs**

```json
{
  "plans": [
    { "id": "free", "name": "Free", "price": 0, "dodo_plan_id": null, ... },
    { "id": "starter_monthly", "name": "Starter", "price": 29, "dodo_plan_id": "plan_starter_monthly", ... },
    ...
  ]
}
```

---

## 7. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-7.1 | `POST /billing/checkout` returns DoDo checkout URL for all 5 plan types |
| AC-7.2 | Webhook verifies DoDo signature and returns 400 on invalid signature |
| AC-7.3 | `checkout.completed` (subscription) → user plan updated, `dodo_customer_id` stored |
| AC-7.4 | `checkout.completed` (credit top-up) → credits added to user's domain via `CreditService.add_bonus` |
| AC-7.5 | `subscription.cancelled` → user downgraded to Free tier |
| AC-7.6 | `GET /billing/portal` returns valid DoDo billing portal URL |
| AC-7.7 | All endpoints return 503 with clear message when `DODO_API_KEY` not set |
| AC-7.8 | Frontend "Upgrade" buttons call new endpoints and redirect to DoDo checkout |
| AC-7.9 | Frontend "Manage Billing" button redirects to DoDo portal URL |

---

## 8. Frontend Changes (apps/web)

### 8.1 Settings Page (`/dashboard/settings/page.tsx`)
- Replace Stripe checkout calls with new `/billing/checkout` endpoint
- Replace "Manage Subscription" with call to `/billing/portal`
- Display current plan from user session

### 8.2 Pricing Page (`/page.tsx` pricing section)
- Update plan IDs if DoDo uses different identifiers
- "Get Started" buttons → call `/billing/checkout` via API client

---

## 9. Testing

| Test | Method |
|---|---|
| Checkout session creation (all 5 plans) | Unit: mock DoDo HTTP, assert URL format |
| Webhook signature verification | Unit: valid HMAC → 200, invalid → 400 |
| Webhook: subscription activation | Integration: mock webhook payload, assert user plan updated |
| Webhook: credit top-up | Integration: mock payload, assert `CreditService.add_bonus` called |
| Webhook: subscription cancellation | Integration: mock payload, assert user downgraded to Free |
| Billing portal URL generation | Unit: mock DoDo, assert URL returned |
| 503 when unconfigured | Unit: unset `DODO_API_KEY`, call endpoint, assert 503 |

---

## 10. Risks

- **DoDo API differences** — If webhook events or checkout flow differ significantly from Stripe assumptions, implementation may need redesign (mitigation: confirm DoDo docs before G1 approval)
- **Sandbox environment** — Need DoDo test mode for CI/CD (mitigation: confirm sandbox availability)
- **Migration data loss** — Renaming `stripe_customer_id` is safe (no Stripe customers exist yet) but must be done in transaction

---

## 11. Rollback

1. Revert `apps/api/app/config.py` to Stripe vars
2. Revert `apps/api/app/routers/billing.py` to Stripe implementation
3. Revert `apps/api/app/models/user.py` column to `stripe_customer_id`
4. Run reverse migration: `ALTER TABLE users RENAME COLUMN dodo_customer_id TO stripe_customer_id;`
5. Revert frontend billing calls

---

## 12. Out of Scope

- Proration handling on plan upgrade/downgrade (defer to Phase 2)
- Invoice PDF generation
- Dunning/retry logic for failed payments (DoDo handles)
- Multi-currency (USD only for MVP)
- Affiliate/referral program