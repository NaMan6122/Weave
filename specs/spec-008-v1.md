# spec-008-v1 — A-B-C Triangulation

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-2.4, FR-2.5
**TDD Refs:** §5.2 (Triangulation Algorithm)

---

## 1. Overview

Triangulation is **implemented** in `apps/api/app/services/triangulation.py`:
- `form_triangle(domain_a, domain_b)` — finds C such that A→B, B→C, C→A with no reciprocal links
- `complete_triangle()` — marks triangle complete when all 3 links are placed
- `check_triangle_health()` — breaks triangle if any link is removed/broken
- `assign_link_to_triangle()` — assigns a link to a slot (ab/bc/ca)
- `find_pending_triangles()` — finds forming triangles needing links
- `_is_compatible()` — niche + DR (±30) compatibility check

**Triangle worker** (`workers/triangle_worker.py`) runs hourly to form triangles for queued requests.

**This spec fills gaps:**
- A. Integration with place_link flow (auto-assign to triangle)
- B. Triangle visualization on dashboard
- C. Multi-hop (A-B-C-D) for Pro tier
- D. Triangle dissolution + cleanup

---

## 2. Gap A — Auto-Assignment on Place Link

### 2.1 Current Issue

`MatchingService.place_link()` creates a Link but doesn't check if it satisfies a pending triangle slot.

### 2.2 Fix

After creating a link in `place_link()`:
```python
# Check if this link satisfies any pending triangle
pending = await TriangulationService.find_pending_triangles(db, source_domain_id)
for triangle in pending:
    if triangle.domain_a_id == source_domain_id and triangle.domain_b_id == target_domain_id:
        await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "ab")
        break
    elif triangle.domain_b_id == source_domain_id and triangle.domain_c_id == target_domain_id:
        await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "bc")
        break
    elif triangle.domain_c_id == source_domain_id and triangle.domain_a_id == target_domain_id:
        await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "ca")
        break
```

### 2.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-2.1 | Placing a link that completes a triangle auto-assigns it |
| AC-2.2 | Triangle status transitions to "complete" when 3rd link placed |

---

## 3. Gap B — Triangle Visualization

### 3.1 Dashboard Display

On `/dashboard/network` or a new `/dashboard/triangles`:
- List of triangles involving user's domains
- Status badge: forming (yellow), complete (green), broken (red)
- Visual: simple A→B→C→A diagram with domain names

### 3.2 API Endpoint

**GET `/api/v1/triangles?domain_id=uuid`**
```json
{
  "triangles": [
    {
      "id": "uuid",
      "domain_a": { "domain": "site-a.com", "dr": 45 },
      "domain_b": { "domain": "site-b.com", "dr": 38 },
      "domain_c": { "domain": "site-c.com", "dr": 52 },
      "status": "complete",
      "links": { "ab": "live", "bc": "live", "ca": "pending" }
    }
  ]
}
```

### 3.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | User can see all triangles they're part of |
| AC-3.2 | Status is accurate (reflects current link states) |

---

## 4. Gap C — Multi-Hop (Phase 2 Stub)

### 4.1 Design Note

A-B-C-D (4-node) and larger chains deferred to Phase 2. The data model supports it (links table + a `chain` or extended triangle table), but the matching complexity grows combinatorially.

For now: document that the `triangles` table could be generalized to a `link_chains` table with N participants.

### 4.2 No implementation needed for MVP.

---

## 5. Gap D — Triangle Dissolution

### 5.1 When

- If a triangle remains "forming" for >30 days with no progress → dissolve
- If a triangle is "broken" for >7 days with no replacement → dissolve

### 5.2 Dissolution

```python
async def dissolve_triangle(db, triangle_id):
    triangle.status = "dissolved"
    # Unlink any assigned links from this triangle
    for link_id in [triangle.link_ab_id, triangle.link_bc_id, triangle.link_ca_id]:
        if link_id:
            link = await db.get(Link, link_id)
            link.triangle_id = None
```

### 5.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | Stale forming triangles dissolved after 30 days |
| AC-5.2 | Dissolved triangle's links remain active (just unlinked from triangle) |

---

## 6. Files to Modify/Create

| File | Change |
|------|--------|
| `apps/api/app/services/matching.py` | Add triangle auto-assignment in place_link |
| `apps/api/app/routers/triangles.py` | Create (list triangles endpoint) |
| `apps/api/app/workers/triangle_worker.py` | Add dissolution logic |

---

## 7. Out of Scope

- Multi-hop chains (Phase 2)
- Triangle preference settings (user can opt out)
- Manual triangle formation request
