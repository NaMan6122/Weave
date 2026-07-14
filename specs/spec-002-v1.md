# spec-002-v1 — Domain Registration & Verification

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-1.2, FR-1.3, FR-1.4, FR-1.5, FR-1.6
**TDD Refs:** §3.1 (domains table), §4.2 (DomainService)

---

## 1. Overview

Domain registration, verification, and vetting are **already implemented**:
- Backend: `apps/api/app/routers/domains.py`, `services/domain.py`, `models/domain.py`
- Frontend: `apps/web/app/dashboard/domains/` (list, add, detail + verify buttons)
- Verification methods: DNS TXT (`_weave.<domain>`), HTML meta tag, `.well-known/weave-verify.txt`
- Vetting: WTS formula, DR/DA/spam/age/traffic/PBN checks, approval/rejection

**This spec documents the existing implementation and fills these gaps:**
- A. Plan-based domain limit enforcement
- B. Periodic re-vetting schedule
- C. PBN detection heuristics (currently just a boolean flag)
- D. Domain pause/resume functionality
- E. Verification instructions UX (frontend copy)

---

## 2. Existing Implementation (Documented)

### 2.1 Registration Flow

```
POST /api/v1/domains/
  Body: { domain, niche?, language?, niche_strict? }
  → Normalize domain (lowercase, strip)
  → Check uniqueness (409 if exists)
  → Generate verification_token (uuid4 hex)
  → Create Domain record (status="pending", verified=false)
  → Create CreditAccount (balance=0)
  → Return DomainResponse
```

### 2.2 Verification Methods

| Method | Mechanism | Lookup |
|--------|-----------|--------|
| `dns` | TXT record `weave-verify=<token>` on `_weave.<domain>` | dnspython → fallback Google DoH |
| `meta` | `<meta name="weave-verify" content="<token>">` on homepage | httpx GET homepage |
| `file` | Token in `https://<domain>/.well-known/weave-verify.txt` | httpx GET file |

```
POST /api/v1/domains/{id}/verify
  Body: { method: "dns" | "meta" | "file" }
  → Lookup token via chosen method
  → If found: set verified=true, trigger vetting
  → If not: return 422 with failure message
```

### 2.3 Vetting (WTS Calculation)

Runs automatically after verification succeeds.

**Metrics fetched** (via `services/metrics.py`): DR, DA, spam_score, organic_traffic, domain_age_days

**Rejection thresholds:**
- DR < 5
- organic_traffic < 500/month
- spam_score >= 15%
- domain_age_days < 180
- is_pbn = true

**WTS formula:**
```
WTS = DA * 0.30 + content_quality * 0.25 + traffic_legitimacy * 0.20
    + link_profile(DR) * 0.15 + age_score * 0.10
```

Where:
- traffic_legitimacy = min(organic_traffic / 1000, 100)
- age_score = min(domain_age_days / 365 * 20, 100)

**Outcome:** `approved` (WTS >= 30) or `rejected` (with reasons).

---

## 3. Gap A — Plan-Based Domain Limits

### 3.1 Limits

| Plan | Max Domains |
|------|-------------|
| free | 5 |
| starter | 25 |
| pro | 100 |
| agency | unlimited (no cap) |

### 3.2 Enforcement

In `DomainService.create_domain()`, before creating the domain:

```python
PLAN_LIMITS = {"free": 5, "starter": 25, "pro": 100, "agency": None}

async def _check_domain_limit(db, user_id, plan):
    if PLAN_LIMITS[plan] is None:
        return  # unlimited
    count = await db.scalar(
        select(func.count(Domain.id))
        .where(Domain.user_id == user_id, Domain.status != "removed")
    )
    if count >= PLAN_LIMITS[plan]:
        raise ValueError(f"Domain limit reached ({PLAN_LIMITS[plan]} for {plan} plan)")
```

### 3.3 API Change

`POST /api/v1/domains/` returns **403** (not 409) when plan limit is reached:
```json
{ "detail": "Domain limit reached (5 for free plan). Upgrade to add more." }
```

### 3.4 Frontend

- On `/dashboard/domains/add`, if at limit: disable "Add Domain" button, show upgrade CTA
- Show current usage: "3 of 5 domains used" in domain list header

### 3.5 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Free user cannot add 6th domain (gets 403) |
| AC-3.2 | Removed domains don't count toward limit |
| AC-3.3 | Upgrading plan immediately allows adding more domains |
| AC-3.4 | Agency plan has no cap |

---

## 4. Gap B — Periodic Re-Vetting

### 4.1 Schedule

- **Weekly metrics refresh** (via `metrics_worker`): updates DR, DA, organic_traffic, spam_score for all active domains
- **Monthly re-vetting**: recalculates WTS from refreshed metrics, may change vetting_status

### 4.2 Re-Vetting Rules

- If WTS drops below 20 (not 30 — hysteresis to avoid flapping): status → `suspended`
- If spam_score rises above 20%: status → `suspended`
- Suspended domains don't participate in matching but links remain live
- User is notified (webhook `domain.suspended` + dashboard alert)
- User can appeal or fix issues and request manual re-vet

### 4.3 Worker Implementation

Add to `metrics_worker.py` (already scheduled weekly):
```python
# After refreshing metrics, check if re-vet needed:
if domain.wts < 20 or domain.spam_score > 20:
    domain.vetting_status = "suspended"
    domain.status = "suspended"
    # queue webhook domain.suspended
```

### 4.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Weekly worker updates DR/DA/traffic for all active domains |
| AC-4.2 | Domain with WTS < 20 after refresh gets suspended |
| AC-4.3 | Suspended domain excluded from matching results |
| AC-4.4 | User sees suspension reason on domain detail page |

---

## 5. Gap C — PBN Detection Heuristics

### 5.1 Signals (Phase 1 — MVP)

For MVP, PBN detection is **lightweight** (deep detection deferred to Phase 2):

1. **Shared hosting fingerprint**: Reverse-IP lookup — if >50 domains on same IP and >30% have DR <10, flag
2. **Thin content**: If homepage word count < 300, flag for manual review
3. **WHOIS clustering**: If user's other domains share registrant email with known spam networks (checked against a maintained list), flag

### 5.2 Implementation

Add to `DomainService.vet_domain()` a call to `_check_pbn_signals()`:
```python
async def _check_pbn_signals(domain_name: str) -> bool:
    # Phase 1: only check homepage content length
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://{domain_name}")
            if len(resp.text.split()) < 300:
                return True  # suspected PBN/thin site
    except:
        pass
    return False
```

Full IP-clustering and WHOIS checks deferred to Phase 2 (requires external API budget).

### 5.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | Site with <300 words on homepage gets is_pbn=true |
| AC-5.2 | PBN-flagged domain gets rejected with reason |

---

## 6. Gap D — Domain Pause/Resume

### 6.1 Behavior

Users can pause a domain to temporarily opt out of matching without losing credit history.

```
POST /api/v1/domains/{id}/pause
  → domain.status = "paused"
  → Paused domains excluded from matching
  → Existing placed links remain (not removed)
  → Credits stop accruing for this domain

POST /api/v1/domains/{id}/resume
  → domain.status = "active" (only if vetting_status = "approved")
  → Domain re-enters matching pool
```

### 6.2 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | Paused domain doesn't appear in matching results |
| AC-6.2 | Paused domain's existing links remain live |
| AC-6.3 | Resume fails if domain is suspended or rejected |

---

## 7. Gap E — Verification Instructions UX

### 7.1 Frontend Copy

On `/dashboard/domains/[id]` (when unverified), show clear instructions for each method:

**DNS Tab:**
> Add a TXT record to your DNS:
> - Host: `_weave.yourdomain.com`
> - Value: `weave-verify=<token>`
> - TTL: 300 (or lowest available)
> DNS changes may take up to 48 hours to propagate.

**Meta Tag Tab:**
> Add this tag inside `<head>` on your homepage:
> ```html
> <meta name="weave-verify" content="<token>">
> ```

**File Upload Tab:**
> Create a file at: `https://yourdomain.com/.well-known/weave-verify.txt`
> File contents (just the token, nothing else):
> ```
> <token>
> ```

Each tab has a "Verify Now" button that calls the verify endpoint.

### 7.2 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-7.1 | Verification token is displayed on domain detail page |
| AC-7.2 | Instructions are shown for all 3 methods with the actual token |
| AC-7.3 | "Verify Now" button triggers verification and shows success/failure |

---

## 8. Files to Modify

| File | Change |
|------|--------|
| `apps/api/app/services/domain.py` | Add plan limit check, pause/resume, PBN heuristic |
| `apps/api/app/routers/domains.py` | Add pause/resume endpoints, change limit error to 403 |
| `apps/api/app/workers/metrics_worker.py` | Add re-vetting logic after metrics refresh |
| `apps/web/app/dashboard/domains/add/page.tsx` | Show limit usage + upgrade CTA |
| `apps/web/app/dashboard/domains/[id]/page.tsx` | Verification instructions copy |

---

## 9. Out of Scope

- Custom niche taxonomy (use free-text for now, structured taxonomy in Phase 2)
- Bulk domain import (Agency feature, Phase 3)
- Domain transfer between users
- Cross-language matching opt-in UI
