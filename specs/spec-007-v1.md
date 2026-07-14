# spec-007-v1 — Dashboard MVP

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-6.1, FR-6.2, FR-6.3, FR-6.4, FR-6.5, FR-6.6
**TDD Refs:** §4.3 (Web Application)

---

## 1. Overview

Dashboard pages **already exist** at `apps/web/app/dashboard/`:
- `/dashboard` — overview with stat cards, recent links
- `/dashboard/domains` — domain list
- `/dashboard/domains/[id]` — domain detail + verify buttons
- `/dashboard/domains/add` — add domain form
- `/dashboard/links` — link log
- `/dashboard/credits` — credit balance/history
- `/dashboard/analytics` — analytics page
- `/dashboard/network` — network browser
- `/dashboard/api-keys` — API key management
- `/dashboard/settings` — account settings

**This spec fills gaps:**
- A. Domain switcher (multi-domain context)
- B. Real-time notifications (link removed, credit low)
- C. Link health status badges + filtering
- D. ROI estimator widget
- E. CSV export for agency users

---

## 2. Gap A — Domain Switcher

### 2.1 Behavior

- Dropdown in dashboard sidebar/header showing all user's active domains
- Selected domain filters all data (credits, links, analytics) to that domain
- "All Domains" option shows aggregate
- Persists selection in URL query param (`?domain=uuid`) or localStorage

### 2.2 Implementation

Component: `apps/web/components/dashboard/domain-switcher.tsx`
- Fetches `GET /api/v1/domains/` on mount
- Stores selection in React context (DomainContext)
- All dashboard pages consume context to filter API calls

### 2.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-2.1 | Switching domain updates all dashboard data |
| AC-2.2 | "All Domains" shows aggregated stats |
| AC-2.3 | Selection persists across page navigation |

---

## 3. Gap B — Real-Time Notifications

### 3.1 MVP Approach (Polling)

No WebSocket for MVP. Poll `/api/v1/notifications` every 60 seconds.

### 3.2 Notification Types

| Type | Trigger | Display |
|------|---------|---------|
| `link_removed` | Link status → removed | Red badge + toast |
| `link_placed` | New backlink placed to your domain | Green badge + toast |
| `credits_low` | Balance < 10 | Yellow banner |
| `domain_vetted` | Vetting complete (approved/rejected) | Blue badge |

### 3.3 Backend Endpoint

**GET `/api/v1/notifications`**
```json
{
  "notifications": [
    { "id": "uuid", "type": "link_removed", "message": "...", "read": false, "created_at": "..." }
  ],
  "unread_count": 3
}
```

### 3.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Unread notification count shown in sidebar |
| AC-3.2 | Clicking notification marks it read |
| AC-3.3 | Toast appears for new notifications |

---

## 4. Gap C — Link Health Badges & Filtering

### 4.1 Link Table Enhancement

On `/dashboard/links`:
- Status badges: green (live), yellow (modified), red (removed), gray (broken)
- Filter tabs: All | Live | Pending | Removed | Broken
- Sort by: date placed, match score, status

### 4.2 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Color-coded status badges on each link row |
| AC-4.2 | Filter tabs correctly filter the table |

---

## 5. Gap D — ROI Estimator

### 5.1 Formula

```
Estimated ROI = total_backlinks_earned * avg_cost_per_link_in_industry
```

Where `avg_cost_per_link` = $150 (configurable constant, industry average).

### 5.2 Display

Card on overview page: "Estimated value of backlinks earned: $X,XXX"
Subtitle: "Based on industry average of $150/link"

### 5.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | ROI card shows on overview page |
| AC-5.2 | Value updates when new links are earned |

---

## 6. Gap E — CSV Export

### 6.1 Endpoints

**GET `/api/v1/links/export?format=csv&domain_id=uuid`**
- Returns CSV with: date, source_url, target_url, anchor_text, match_score, status, credits

**GET `/api/v1/credits/export?format=csv&domain_id=uuid`**
- Returns CSV with: date, type, amount, description, balance_after

### 6.2 Plan Gating

- Free/Starter: no export (button disabled, shows upgrade CTA)
- Pro/Agency: full export

### 6.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | Pro user can download CSV of links |
| AC-6.2 | Free user sees upgrade prompt |

---

## 7. Files to Modify/Create

| File | Change |
|------|--------|
| `apps/web/components/dashboard/domain-switcher.tsx` | Create/update with context |
| `apps/web/lib/domain-context.tsx` | Create (React context for selected domain) |
| `apps/api/app/routers/notifications.py` | Create |
| `apps/api/app/models/notification.py` | Create |
| `apps/api/app/routers/links.py` | Add export endpoint |
| `apps/api/app/routers/credits.py` | Add export endpoint |

---

## 8. Out of Scope

- WebSocket real-time updates (Phase 2)
- White-label dashboard for agencies (Phase 3)
- PDF export (Phase 3)
- Custom dashboard widgets
