# spec-009-v1 — Landing Page & Documentation

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** Phase 1 MVP (Landing page + docs)
**TDD Refs:** §4.3 (Marketing pages)

---

## 1. Overview

A landing page **already exists** at `apps/web/app/page.tsx`:
- Hero, How It Works, Features grid, Comparison table, Pricing, MCP setup, CTA, Footer

**This spec fills gaps:**
- A. Docs site (MCP setup guide, API reference link, FAQ)
- B. Pricing page (dedicated, with feature comparison matrix)
- C. Blog scaffold (for content marketing / SEO)
- D. SEO metadata + OpenGraph
- E. Analytics integration (Plausible or PostHog)

---

## 2. Gap A — Documentation Pages

### 2.1 Route: `/docs`

Sections (simple MDX or inline pages for MVP):

1. **Getting Started** — Register → Add domain → Verify → Get API key → Install MCP
2. **MCP Setup** — Claude Desktop config, Claude Code CLI, env vars
3. **How Matching Works** — Brief explanation of scoring, niche, DR
4. **Credit System** — How you earn, how you spend, expiry
5. **FAQ** — Common questions (Is this safe? Will Google penalize? etc.)
6. **API Reference** — Link to auto-generated OpenAPI docs at `/api/docs`

### 2.2 Implementation

- Use Next.js static pages (`apps/web/app/(marketing)/docs/[slug]/page.tsx`)
- Content stored as MDX files in `apps/web/content/docs/`
- Simple TOC sidebar
- No external docs platform needed for MVP

### 2.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-2.1 | All 6 doc sections are accessible and readable |
| AC-2.2 | MCP setup guide includes copy-paste config snippets |
| AC-2.3 | FAQ addresses Google penalty concern |

---

## 3. Gap B — Pricing Page

### 3.1 Route: `/pricing`

Dedicated page with:
- Feature comparison matrix (4 tiers × all features)
- Toggle: monthly / annual (20% discount)
- CTA buttons linking to registration with plan pre-selected
- "Most popular" badge on Pro
- FAQ section specific to pricing

### 3.2 Already Exists (Partial)

The landing page has a pricing section. Dedicated `/pricing` page should expand it with full feature matrix.

### 3.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | All plan features from PRD §4 displayed accurately |
| AC-3.2 | Annual toggle shows discounted prices |
| AC-3.3 | CTA leads to /register?plan=starter etc. |

---

## 4. Gap C — Blog Scaffold

### 4.1 Route: `/blog`

- Simple blog listing page
- Individual posts at `/blog/[slug]`
- MDX-based (same pattern as docs)
- Categories: guides, announcements, seo-tips

### 4.2 Initial Posts (Content Needed)

1. "Introducing Weave: AI-Native Backlink Exchange"
2. "How to Set Up Weave with Claude Desktop"
3. "Why A-B-C Link Building Beats Direct Reciprocal Links"

### 4.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Blog listing page renders MDX posts |
| AC-4.2 | Posts have proper meta (title, description, date, author) |
| AC-4.3 | RSS feed at `/blog/feed.xml` (optional for MVP) |

---

## 5. Gap D — SEO Metadata

### 5.1 Per-Page Metadata

Every public page needs:
- `<title>` — unique, ≤60 chars
- `<meta name="description">` — unique, ≤155 chars
- OpenGraph tags (og:title, og:description, og:image, og:url)
- Twitter card meta
- Canonical URL

### 5.2 Implementation

Use Next.js `metadata` export in each page/layout:
```tsx
export const metadata: Metadata = {
  title: "Weave — AI-Native Backlink Exchange",
  description: "Automated link building for AI-powered publishers...",
  openGraph: { ... },
}
```

### 5.3 OG Image

Generate a default OG image (1200×630) with Weave branding. Static file in `public/og-image.png`.

### 5.4 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | Every public page has unique title + description |
| AC-5.2 | OG image displays correctly when shared on Twitter/LinkedIn |
| AC-5.3 | Canonical URLs set on all pages |

---

## 6. Gap E — Analytics

### 6.1 Choice: Plausible (Privacy-First)

- No cookies, GDPR-compliant out of the box
- Simple script tag, no npm package needed
- Self-hosted or cloud ($9/mo for 10K pageviews)

### 6.2 Implementation

Add to `apps/web/app/layout.tsx`:
```tsx
<Script
  defer
  data-domain="getweave.io"
  src="https://plausible.io/js/script.js"
/>
```

### 6.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | Page views tracked on all public pages |
| AC-6.2 | No cookie banner needed (privacy-first analytics) |

---

## 7. Files to Create/Modify

| File | Change |
|------|--------|
| `apps/web/app/(marketing)/docs/page.tsx` | Create (docs index) |
| `apps/web/app/(marketing)/docs/[slug]/page.tsx` | Create (doc reader) |
| `apps/web/content/docs/` | Create (MDX content files) |
| `apps/web/app/(marketing)/pricing/page.tsx` | Create/update |
| `apps/web/app/(marketing)/blog/page.tsx` | Create (blog listing) |
| `apps/web/app/(marketing)/blog/[slug]/page.tsx` | Create (blog post) |
| `apps/web/app/layout.tsx` | Add OG defaults + analytics script |
| `apps/web/public/og-image.png` | Create |

---

## 8. Out of Scope

- Custom CMS for blog (use MDX files for MVP)
- Internationalization (i18n) of marketing pages
- A/B testing on landing page
- Video content / tutorials
