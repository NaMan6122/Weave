# Agent Memory

## Session Summary
Last Session: 2026-07-14 14:00
Active Task: T-003 — Wire missing MCP tools + error handling — PENDING
Last File Touched: apps/api/tests/test_credits.py (updated test expectations)
Immediate Next Step: Audit and fix auth holes in domains/link/admin routers

## Active Task
T-001 — Implement credit_value() PRD formula & fix credit calculations
State: COMPLETED ✅
Completed: 2026-07-14 14:15
Weight: SIGNIFICANT
Spec Reference: spec-003-v1.md §2 (Credit Formula Decision), DCL-001

## Task Log
### 2026-07-14 14:00 — T-001: Implement credit_value() PRD formula & fix credit calculations
**Goal:** Implement the missing `credit_value()` function from the PRD formula `max(1, int(log10(max(dr,1)+1) * 100))`; fix `calculate_credits_earned()` and `calculate_credits_required()` to match the spec; update tests to pass.
**Spec Reference:** spec-003-v1.md §2.3, DCL-001
**Approach:**
   1. Read existing `services/credits.py`
   2. Read `tests/test_credits.py`
   3. Read `scripts/seed.py`
   4. Implement `credit_value()` function
   5. Fix `calculate_credits_earned()` and `calculate_credits_required()` to PRD formula
   6. Fix webhook events nullable mismatch (model said nullable=True, migration says nullable=False)
   7. Update tests with correct PRD expected values
   8. Run full test suite
**Checklist:**
  - [x] Step 1: Read existing credit service code
  - [x] Step 2: Read tests and seed script
  - [x] Step 3: Implement credit_value()
  - [x] Step 4: Fix credit calculation formulas
  - [x] Step 5: Fix webhook model-migration mismatch
  - [x] Step 6: Update tests
  - [x] Step 7: Run tests to verify (33/33 passed)
**Outcome:** DCL-001 (PRD formula deviation) fully implemented. 
  - `credit_value(dr)` added as standalone log formula for seed scripts
  - `calculate_credits_earned()` uses PRD: `10 * (DR/50) * (match_score/100) * placement_mult` (min 1)
  - `calculate_credits_required()` uses tiered multipliers
  - Webhook `events` column: model changed from `dict | None` to `dict` with `default=dict` to match `nullable=False` migration
  - Tests updated with correct PRD values (earned DR50=7.00, required DR50=20.00)
**Test Evidence:** All 33 tests pass (10 pure calc + 3 DB-backed credit + 4 auth + 9 API + 7 embeddings)
**Blockers:** NONE
**Rollback:** Revert changes to `apps/api/app/services/credits.py`, `apps/api/app/models/webhook.py`, and `apps/api/app/tests/`

### 2026-07-14 14:20 — T-002: Fix authorization holes on 7 endpoints
**Goal:** Prevent authenticated users from accessing/modifying domains and credit accounts they don't own.
**Spec Reference:** General security hardening (no spec deviation — filling gaps)
**Changes Made:**
  - `apps/api/app/routers/domains.py`:
    - Added `_require_domain_owner()` helper that queries domain + user_id + eager-loads credit_account
    - `GET /domains/{id}` — now checks domain ownership
    - `POST /domains/{id}/verify` — now checks domain ownership before verification
    - `POST /domains/{id}/vet` — now checks domain ownership before vetting
    - `GET /domains/by-name/{name}/status` — now filters by user_id
  - `apps/api/app/routers/credits.py`:
    - Added `_require_credit_domain()` helper
    - `GET /credits/balance/{id}` — now checks domain ownership
    - `GET /credits/balance/by-name/{name}` — now filters by user_id
    - `GET /credits/history/{id}` — now checks domain ownership
**Test Evidence:** All 33 tests pass (no regressions).
**Outcome:** 7 auth holes closed. All domain and credit endpoints now enforce user_id ownership.

## Self-Corrections
(none)

## Open Questions
- All 9 existing specs are marked DRAFT awaiting G1 approval. Per §4.2, only a human can promote to ACTIVE. T-001 references spec-003 which has an accepted deviation (DCL-001). Proceeded with implementation per spec content since deviation was human-logged.
