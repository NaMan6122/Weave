# spec-003-v1 — Credit System

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-3.6
**TDD Refs:** §3.1 (credit_accounts, credit_transactions), §5.3 (Credit Calculation)

---

## 1. Overview

The credit system is **implemented** in:
- `apps/api/app/services/credits.py` — earn, spend, reverse, bonus, expire, balance, history
- `apps/api/app/models/credit.py` — CreditAccount, CreditTransaction
- `apps/api/app/routers/credits.py` — balance, history, bonus endpoints

**Existing implementation notes:**
- Uses `log10(DR+1) * 100` for credit value (diverges from PRD's `base_credit * DR/50 * relevance * placement_quality`)
- Expiry logic exists (180 days) but is complex and may have edge cases
- Transaction types: `earned`, `spent`, `reversed`, `bonus`, `expired`

**This spec fills gaps:**
- A. Align credit formula with PRD (or document the deviation)
- B. Monthly plan bonus credits
- C. Credit low-balance warning
- D. Credit transfer between domains (same owner)
- E. Expiry worker scheduling + 30-day warning email
- F. Dashboard credit page (frontend)

---

## 2. Credit Formula Decision

### 2.1 Current Implementation

```python
credits = max(1, int(log10(max(DR, 1) + 1) * 100))
# DR 10 → 104, DR 30 → 148, DR 50 → 171, DR 80 → 190
# Same formula for earned and required (symmetric)
```

### 2.2 PRD Formula

```python
# Earned:
credits_earned = 10 * (source_DR / 50) * (match_score / 100) * placement_multiplier
# DR 50, score 80, body → 10 * 1.0 * 0.8 * 1.0 = 8.0

# Required:
credits_required = 10 * DR_tier_multiplier
# DR 50 → 10 * 2.0 = 20
```

### 2.3 Decision: Adopt PRD Formula

The PRD formula is superior — it accounts for relevance and placement quality, creates asymmetry that incentivizes high-quality placements, and discourages low-effort link spam. The current log-based formula is simpler but doesn't differentiate by quality.

**Status:** DECIDED — adopt PRD formula. This is a spec deviation (DCL-001) from the current implementation.

**Changes to `services/credits.py`:**

```python
def calculate_credits_earned(
    source_dr: float,
    match_score: float,
    placement_type: str = "body",
) -> Decimal:
    BASE_CREDIT = Decimal("10")
    dr_multiplier = Decimal(str(source_dr / 50))
    relevance_multiplier = Decimal(str(match_score / 100))
    placement_multiplier = {
        "body": Decimal("1.0"),
        "sidebar": Decimal("0.5"),
        "footer": Decimal("0.3"),
        "author_bio": Decimal("0.3"),
    }[placement_type]
    return (BASE_CREDIT * dr_multiplier * relevance_multiplier * placement_multiplier).quantize(Decimal("0.01"))

def calculate_credits_required(target_dr: float) -> Decimal:
    BASE_COST = Decimal("10")
    if target_dr <= 20: multiplier = Decimal("0.5")
    elif target_dr <= 40: multiplier = Decimal("1.0")
    elif target_dr <= 60: multiplier = Decimal("2.0")
    elif target_dr <= 80: multiplier = Decimal("4.0")
    else: multiplier = Decimal("8.0")
    return (BASE_COST * multiplier).quantize(Decimal("0.01"))
```

---

## 3. Gap B — Monthly Plan Bonus Credits

### 3.1 Bonus Schedule

| Plan | Monthly Bonus |
|------|--------------|
| free | 0 |
| starter | +10% of earned that month (min 5 credits) |
| pro | +25% of earned that month (min 15 credits) |
| agency | +50% of earned that month (min 30 credits) |

### 3.2 Implementation

New worker: `bonus_worker.py` — runs on 1st of each month.

```python
async def distribute_monthly_bonuses(db: AsyncSession):
    """Calculate and distribute plan bonuses based on last month's earnings."""
    # For each active domain with a paid plan:
    #   sum earned transactions from last calendar month
    #   calculate bonus = max(earned * plan_percentage, min_bonus)
    #   call CreditService.add_bonus()
```

### 3.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Starter user who earned 100 credits last month gets 10 bonus credits on 1st |
| AC-3.2 | Pro user who earned 0 credits still gets minimum 15 bonus |
| AC-3.3 | Free users get no bonus |
| AC-3.4 | Bonus transaction appears in history with type "bonus" and description |

---

## 4. Gap C — Low Balance Warning

### 4.1 Trigger

When a credit account balance drops below **10 credits** after a spend transaction:
- Fire webhook event `credits.low` (if subscribed)
- Send email notification (via Resend, if configured)
- Show banner on dashboard

### 4.2 Threshold Configuration

Default threshold: 10 credits. Future: user-configurable per domain (Phase 3).

### 4.3 Implementation

In `CreditService.spend_credits()`, after successful spend:
```python
if account.balance < Decimal("10"):
    await notify_low_balance(account)
```

### 4.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Spending credits that drops balance below 10 triggers notification |
| AC-4.2 | Notification is not re-sent until balance goes above 10 and drops again |
| AC-4.3 | Webhook `credits.low` fires with domain_id and current balance |

---

## 5. Gap D — Credit Transfer Between Domains

### 5.1 Rules

- Only between domains owned by the same user
- Cannot transfer more than current balance
- Both domains must be active and approved
- Transaction recorded on both accounts

### 5.2 API Endpoint

**POST `/api/v1/credits/transfer`**
```json
{
  "from_domain_id": "uuid",
  "to_domain_id": "uuid",
  "amount": 25.00
}
```

Response 200:
```json
{
  "from_balance": 75.00,
  "to_balance": 50.00,
  "amount_transferred": 25.00
}
```

Response 400: insufficient balance, same domain, different owner, inactive domain.

### 5.3 Implementation

```python
async def transfer_credits(
    db, from_domain_id, to_domain_id, amount, user_id
) -> tuple[CreditAccount, CreditAccount]:
    # Verify same owner for both domains
    # Verify both active+approved
    # Debit from_account (type="spent", description="Transfer to {domain}")
    # Credit to_account (type="earned", description="Transfer from {domain}")
```

### 5.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | Transfer between same-owner domains succeeds |
| AC-5.2 | Transfer between different owners returns 403 |
| AC-5.3 | Transfer more than balance returns 400 |
| AC-5.4 | Both transaction logs show the transfer |

---

## 6. Gap E — Expiry Worker Refinement

### 6.1 Current Issues

The existing `expire_old_credits()` method has complex logic for tracking which transactions are already expired. Simplification:

### 6.2 Simplified Approach

Instead of per-transaction expiry tracking, use a **FIFO balance expiry model**:
- Each earned/bonus transaction has a `created_at`
- Credits are consumed FIFO (oldest first) when spent
- Expiry worker: sum all earned/bonus transactions older than 180 days, subtract all spent/expired transactions, expire the remainder

### 6.3 Warning Email

At 150 days (30 days before expiry):
- Send email: "You have {X} credits expiring in 30 days. Use them or lose them!"
- Only send once per batch of expiring credits

### 6.4 Worker Schedule

- `expiry_worker`: runs daily at 02:00 UTC
- `expiry_warning_worker`: runs daily at 10:00 UTC (150-day check)

### 6.5 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | Credits older than 180 days are expired |
| AC-6.2 | Expired credits reduce balance (never below 0) |
| AC-6.3 | Warning email sent at 150 days |
| AC-6.4 | Already-spent credits are not double-expired |

---

## 7. Gap F — Dashboard Credits Page

### 7.1 Route: `/dashboard/credits`

**Components:**
- **Balance card**: Current balance, lifetime earned, lifetime spent
- **Transaction table**: paginated, filterable by type (earned/spent/bonus/expired/reversed)
- **Expiry warning**: "X credits expiring in the next 30 days"
- **Transfer button**: Opens modal to transfer between user's domains

### 7.2 Data Fetching

- `GET /api/v1/credits/balance/{domain_id}` — balance card
- `GET /api/v1/credits/history/{domain_id}?limit=50&offset=0` — transaction table
- Domain switcher in dashboard layout determines which domain's credits to show

### 7.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-7.1 | Credits page shows balance, lifetime earned, lifetime spent |
| AC-7.2 | Transaction history is paginated and filterable |
| AC-7.3 | Transfer modal allows selecting target domain and entering amount |

---

## 8. Files to Modify/Create

| File | Change |
|------|--------|
| `apps/api/app/services/credits.py` | Update formula, add transfer, add low-balance notification |
| `apps/api/app/routers/credits.py` | Add transfer endpoint |
| `apps/api/app/workers/bonus_worker.py` | Create (monthly bonus distribution) |
| `apps/api/app/workers/expiry_worker.py` | Refine expiry + add warning email |
| `apps/web/app/dashboard/credits/page.tsx` | Create/update credits dashboard page |

---

## 9. Out of Scope

- Credit purchasing with real money (deferred — may never add, keeps system pure exchange)
- Per-domain configurable low-balance threshold
- Credit marketplace (trading between users)
