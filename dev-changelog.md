# Weave — Dev Changelog

> Immutable audit trail of spec deviations. See `instruction.md` §5 for format.

---

<!-- No entries yet. First entry will be DCL-001. -->

## 2026-05-24 10:00 — DCL-001

**Task Reference:** T-001 (credit formula implementation)
**Spec Affected:** spec-003-v1.md
**Type:** SUBSTITUTION

**Original Spec:**
Credit formula uses `max(1, int(log10(max(DR, 1) + 1) * 100))` — symmetric for earned and required, no relevance or placement quality factor.

**Deviation:**
Adopting PRD formula: `earned = 10 * (DR/50) * (match_score/100) * placement_multiplier` (min 1). Required uses tiered DR multipliers (0.5x–8x). This creates asymmetry rewarding quality.

**Reason:**
PRD formula incentivizes high-quality, relevant placements over volume. It differentiates by placement type (body vs sidebar) and match relevance, which discourages link spam and rewards thoughtful integration.

**Impact:**
- `apps/api/app/services/credits.py` — `calculate_credits_earned` and `calculate_credits_required` signatures change (new params: match_score, placement_type)
- `apps/api/app/services/matching.py` — `place_link()` must pass match_score and placement_type to credit calc
- Existing credit transactions unaffected (historical data stays)
- Standalone `credit_value(dr)` function added for seed scripts (old log formula)

**Spec Updated:** YES — spec-003-v1.md §2.3 updated to mark decision
