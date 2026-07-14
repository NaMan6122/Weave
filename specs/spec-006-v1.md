# spec-006-v1 — Link Validator & Auto-Replacement

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-5.3, FR-5.4, FR-5.5
**TDD Refs:** §7 (Background Workers — crawl_worker, sla_worker)

---

## 1. Overview

The link validator is **implemented** in `apps/api/app/services/crawler.py`:
- `validate_link()` — fetches source page, checks target URL + anchor text presence
- `_handle_failure()` — credit penalty (2x), credit restoration to target, triangle health check
- `_check_three_strikes()` — suspends domain after 3 failures in 90 days
- `validate_all_links()` — batch validation with per-domain concurrency limit (3)
- `check_sla_expirations()` — marks links past SLA deadline

**Status detection:**
- `live` — target URL + anchor text found
- `modified` — target URL found, anchor text changed
- `removed` — target URL not found on page
- `broken` — page returns 4xx/5xx or network error

**This spec fills gaps:**
- A. Auto-replacement queue for removed/broken links
- B. Webhook events on link status changes
- C. Crawl scheduling (24h cycle via worker)
- D. SLA replacement logic
- E. Notification to affected user

---

## 2. Gap A — Auto-Replacement Queue

### 2.1 Trigger

When a link is marked `removed` or `broken` and:
- The link was placed ≤ SLA period (90 days for Pro, 120 for Agency)
- The target domain (the party who lost the backlink) has remaining SLA coverage

### 2.2 Replacement Flow

```
Link marked removed/broken
  → Check if within SLA period
  → If yes: create replacement_request record
  → replacement_request { target_domain_id, required_dr, niche, status: "pending" }
  → Triangle worker picks up pending requests
  → Finds new source domain with matching criteria
  → Creates new link record (status: "pending_placement")
  → Notifies new source domain's owner via their AI agent's next discover call
```

### 2.3 Database Addition

```sql
CREATE TABLE replacement_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_link_id UUID NOT NULL REFERENCES links(id),
    target_domain_id UUID NOT NULL REFERENCES domains(id),
    required_min_dr  INT,
    required_niche   TEXT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'matched', 'placed', 'expired')),
    matched_link_id  UUID REFERENCES links(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL  -- SLA deadline from original link
);
```

### 2.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-2.1 | Removed link within SLA creates a replacement_request |
| AC-2.2 | Replacement is matched to a domain with similar DR/niche |
| AC-2.3 | Replacement request expires if not fulfilled by original SLA deadline |
| AC-2.4 | Free tier links (no SLA) don't trigger replacement |

---

## 3. Gap B — Webhook Events on Status Changes

### 3.1 Events

| Event | Trigger |
|-------|---------|
| `link.placed` | Link status → `placed` or `live` (first verification) |
| `link.removed` | Link status → `removed` |
| `link.broken` | Link status → `broken` |
| `link.replaced` | Replacement link placed for a removed original |

### 3.2 Implementation

In `validate_link()`, after status change:
```python
if old_status != new_status:
    await webhook_dispatch(
        db,
        domain_id=link.target_domain_id,  # notify the affected party
        event=f"link.{new_status}",
        payload={
            "link_id": str(link.id),
            "source_url": source_page.url,
            "target_url": target_page.url,
            "old_status": old_status,
            "new_status": new_status,
        }
    )
```

### 3.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Webhook fires when link status changes |
| AC-3.2 | Only fires to subscribed users with matching event |
| AC-3.3 | Payload is HMAC-signed with webhook secret |

---

## 4. Gap C — Crawl Worker Scheduling

### 4.1 Schedule

The `crawl_worker` runs daily. Implementation in `workers/crawl_worker.py`:

```python
# APScheduler job (already configured in scheduler.py)
# Runs at 03:00 UTC daily
async def run_crawl_cycle():
    async with get_session() as db:
        summary = await LinkValidatorService.validate_all_links(db)
        await db.commit()
        logger.info(f"Crawl complete: {summary}")
```

### 4.2 Staggering

For large networks, links are processed in batches of 100 with 1-second delay between batches to avoid overwhelming target servers.

### 4.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | All placed/live/modified links are validated within 24h window |
| AC-4.2 | No more than 3 concurrent requests per source domain |
| AC-4.3 | Worker handles individual link failures gracefully (doesn't abort batch) |

---

## 5. Gap D — SLA Worker

### 5.1 Schedule

Runs daily at 04:00 UTC (after crawl worker).

### 5.2 Logic

```python
async def run_sla_check():
    # 1. Check for links past SLA that were removed
    expired = await LinkValidatorService.check_sla_expirations(db)

    # 2. For links removed within SLA, check if replacement was queued
    #    (already handled in _handle_failure → replacement_request)

    # 3. Expire replacement_requests past their deadline
    await expire_stale_replacement_requests(db)
```

### 5.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | Links past SLA are marked `sla_expired` |
| AC-5.2 | Stale replacement requests are expired |

---

## 6. Gap E — User Notifications

### 6.1 When Links Are Removed/Broken

- Dashboard: red badge on "Links" nav item with count of new issues
- Email (if configured): "One of your backlinks was removed" with link details
- Webhook: `link.removed` / `link.broken` (§3 above)

### 6.2 When Replacement Is Placed

- Dashboard: notification in activity feed
- Email: "A replacement backlink has been placed for you"
- Webhook: `link.replaced`

### 6.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | User sees link health issues on dashboard |
| AC-6.2 | Email sent on removal if Resend is configured |

---

## 7. Files to Modify/Create

| File | Change |
|------|--------|
| `apps/api/app/services/crawler.py` | Add webhook dispatch calls, replacement queue creation |
| `apps/api/app/models/replacement.py` | Create (ReplacementRequest model) |
| `apps/api/app/workers/crawl_worker.py` | Create/update (daily crawl job) |
| `apps/api/app/workers/sla_worker.py` | Create (SLA check + replacement expiry) |
| Alembic migration | Add replacement_requests table |

---

## 8. Out of Scope

- Manual re-crawl from dashboard (trigger single link validation) — Phase 2
- Crawl frequency by tier (e.g., Pro gets 12h instead of 24h) — Phase 3
- Screenshot capture of link placement for evidence — Phase 3
