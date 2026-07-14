# Weave — Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2026-05-20
**Status:** Draft

---

## 1. Executive Summary

Weave is an AI-native backlink exchange platform that automates link building by integrating directly into AI content workflows via MCP (Model Context Protocol). Writers and publishers using AI agents earn backlinks by contextually linking to peer sites during content creation — and receive quality inbound links in return through an intelligent, triangulated exchange network.

### Why Now

- AI content production has exploded, but link building remains manual and expensive ($100-500/link via agencies)
- MCP is becoming the standard protocol for AI agent tool integration
- The only competitor (Hrefmatch) is pre-launch with ~72 sites and significant gaps in transparency, matching quality, and developer experience
- There is a clear window to build a technically superior product and capture market share with aggressive pricing

### How We Win

| Dimension         | Hrefmatch                                | Weave                                                      |
| ----------------- | ---------------------------------------- | ---------------------------------------------------------- |
| Matching          | Category-based + DR scoring              | Embedding-based semantic relevance + DR + audience overlap |
| Credit system     | Opaque                                   | Fully transparent with real-time valuation                 |
| Link architecture | A-B-C only                               | A-B-C + configurable multi-hop strategies                  |
| MCP DX            | Single command, minimal tooling          | Rich tool schema, multi-agent support, streaming, webhooks |
| Pricing           | $0 (limited) / $708/yr founding          | $0 (generous) / $29/mo starter / $79/mo pro                |
| Network vetting   | Manual review                            | Automated continuous vetting + community reporting         |
| Link monitoring   | Basic dashboard                          | Real-time monitoring, auto-replacement SLA, alerts         |
| Transparency      | Minimal — no API docs, no credit formula | Full API docs, open credit formula, link quality scores    |

---

## 2. Target Users

### Primary Personas

**1. AI-First Publisher (Solo/Small Team)**

- Publishes 10-50 articles/month using Claude, ChatGPT, or Cursor
- Needs backlinks but can't afford agencies or manual outreach
- Wants a hands-off solution that works inside their existing workflow
- Technical enough to set up an MCP server

**2. Content Agency / SEO Agency**

- Manages 10-100+ client domains
- Needs scalable link building across multiple niches
- Values reporting, transparency, and ROI metrics for client presentations
- Willing to pay more for quality and guarantees

**3. SaaS / Startup Marketing Team**

- Runs a company blog as a growth channel
- Needs domain authority growth to compete in organic search
- Values integration with existing content pipelines (n8n, Make, custom)
- Cares about link relevance and brand safety

### Secondary Personas

**4. Niche Blogger / Affiliate Marketer**

- Runs 1-5 sites in specific verticals
- Very cost-sensitive, needs the free tier to be genuinely useful
- Judges platform by actual DR improvement over time

---

## 3. Core Product Requirements

### 3.1 Domain Registry & Onboarding

**FR-1.1:** Users can register via email, Google, or GitHub OAuth.

**FR-1.2:** Users can add domains with ownership verification via:

- DNS TXT record
- HTML meta tag
- File upload to `.well-known/weave-verify.txt`

**FR-1.3:** Each domain undergoes automated vetting on registration:

- Domain age check (minimum 3 months)
- DR/DA score retrieval (via Moz, Ahrefs API, or DataForSEO)
- Spam score check
- PBN pattern detection (shared hosting fingerprints, interlinking patterns, WHOIS clustering)
- Content quality scoring (AI-generated quality assessment of 5 random pages)
- Organic traffic estimation

**FR-1.4:** Domains are assigned a **Weave Trust Score (WTS)** — a composite 0-100 score combining:

- Domain authority (30%)
- Content quality (25%)
- Traffic legitimacy (20%)
- Link profile health (15%)
- Domain age (10%)

**FR-1.5:** Domains below WTS threshold (configurable, default 30) are rejected with specific feedback on what to improve.

**FR-1.6:** Free tier allows up to 5 domains. Paid tiers allow 25/100/unlimited.

### 3.2 Matching Engine

**FR-2.1:** Every registered page/article is embedded using a sentence-transformer model into a vector space for semantic matching.

**FR-2.2:** When an AI agent requests link opportunities via MCP, the matching engine returns candidates ranked by:

- **Semantic relevance** (cosine similarity of content embeddings) — 40% weight
- **DR/WTS tier proximity** — 25% weight
- **Audience overlap signals** (shared keyword rankings, similar traffic sources) — 20% weight
- **Freshness** (recently published content preferred) — 10%
- **Network diversity** (avoid over-linking to same domains) — 5%

**FR-2.3:** Matching respects exclusion rules:

- Never match competitors (user-defined blocklist)
- Never match same-owner domains
- Language must match (or user opts into cross-language)
- Niche constraints (user can set strict or flexible niche matching)

**FR-2.4:** A-B-C triangulation: Site A links to Site B, Site B links to Site C, Site C links to Site A — no direct reciprocal links. The engine must form valid triangles before confirming placements.

**FR-2.5:** Multi-hop strategies (A-B-C-D) available on Pro tier for lower footprint.

**FR-2.6:** Match quality score is shown to users before confirmation (1-100 with breakdown).

### 3.3 Credit System

**FR-3.1:** Credits are the internal currency. Transparent formula:

```
Credits earned per outbound link = base_credit * DR_multiplier * relevance_multiplier * placement_quality
```

Where:

- `base_credit` = 10
- `DR_multiplier` = linking_site_DR / 50 (normalized)
- `relevance_multiplier` = match_score / 100
- `placement_quality` = 1.0 (body), 0.5 (sidebar/footer), 0.3 (author bio)

**FR-3.2:** Credits required per inbound link:

```
Credits required = base_cost * target_DR_tier_multiplier
```

Where:

- `base_cost` = 10
- DR 0-20: multiplier 0.5
- DR 21-40: multiplier 1.0
- DR 41-60: multiplier 2.0
- DR 61-80: multiplier 4.0
- DR 81+: multiplier 8.0

**FR-3.3:** Credit balance is visible in real-time on dashboard and via API.

**FR-3.4:** Credits expire after 180 days to prevent hoarding and ensure network liquidity.

**FR-3.5:** Negative credit balance is not allowed — placements queue until credits are available.

**FR-3.6:** Credit transaction history with full audit trail.

### 3.4 MCP Server

**FR-4.1:** MCP server exposes the following tools:

| Tool                   | Description                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `weave_discover_links` | Given content draft, returns ranked link opportunities with anchor text suggestions |
| `weave_place_link`     | Confirms an outbound link placement, earns credits                                  |
| `weave_check_balance`  | Returns current credit balance and pending placements                               |
| `weave_domain_status`  | Returns WTS, DR, and vetting status for user's domains                              |
| `weave_link_health`    | Checks status of placed links (live/removed/broken)                                 |

**FR-4.2:** The `weave_discover_links` tool accepts:

- `content` (string): The article content or draft
- `url` (string): The target URL where content will be published
- `max_results` (int, default 5): Number of suggestions
- `niche_strict` (bool, default false): Strict vs flexible niche matching
- `min_dr` (int, optional): Minimum DR of suggested targets
- `exclude_domains` (string[], optional): Domains to exclude

**FR-4.3:** Response includes for each suggestion:

- Target URL and page title
- Match score with breakdown (semantic, DR, audience, freshness)
- Suggested anchor text (3 variations: exact, natural, branded)
- Suggested insertion point in the content
- Credits that would be earned

**FR-4.4:** MCP server supports streaming responses for large result sets.

**FR-4.5:** Authentication via API key passed as MCP server environment variable.

**FR-4.6:** Rate limiting: 100 requests/hour (free), 1000/hour (starter), 5000/hour (pro), unlimited (agency).

### 3.5 Link Placement & Validation

**FR-5.1:** When a user's AI agent places an outbound link (via `weave_place_link`), the system:

1. Validates the target URL is still in the network and active
2. Validates the content context is relevant (re-embeds the surrounding paragraph)
3. Awards credits
4. Queues a corresponding inbound link for the user based on credit balance

**FR-5.2:** Inbound link placement is handled by the receiving site's AI agent during its next content creation cycle, or via a manual placement prompt.

**FR-5.3:** Link validator crawls all placed links every 24 hours:

- **Live**: Link found, anchor text matches, page is indexed
- **Modified**: Link found but anchor text changed
- **Removed**: Link no longer present on page
- **Broken**: Page returns 4xx/5xx

**FR-5.4:** If a link is removed within 30 days of placement:

- Credits are reversed from the remover's account
- A replacement link is queued for the affected party
- Repeat offenders (3+ removals in 30 days) get flagged for review

**FR-5.5:** Link survival SLA: placed links guaranteed for minimum 90 days. If removed by partner, Weave auto-queues a replacement from the network.

### 3.6 Dashboard & Analytics

**FR-6.1:** Multi-domain dashboard with domain switcher.

**FR-6.2:** Per-domain metrics:

- Weave Trust Score (WTS) trend over time
- DR/DA trajectory (pulled weekly)
- Total backlinks earned via Weave
- Credit balance and transaction history
- Link health overview (live/pending/removed/broken)
- Top linking partners
- Niche distribution of inbound links

**FR-6.3:** Link log table with:

- Date placed
- Source URL → Target URL
- Anchor text
- Match score
- Status (live/pending/removed/broken)
- Credits earned/spent

**FR-6.4:** Exportable reports (CSV, PDF) for agency users.

**FR-6.5:** Real-time notifications:

- New backlink placed
- Link removed (with auto-replacement status)
- Domain vetting status change
- Credit balance low warning

**FR-6.6:** ROI estimator: shows estimated $ value of backlinks earned based on industry average cost-per-link.

### 3.7 REST API

**FR-7.1:** Full REST API mirroring all MCP tool capabilities plus:

- Domain management (CRUD)
- Credit management (balance, history, transfer between domains)
- Link management (list, filter, export)
- Webhook configuration
- Analytics endpoints

**FR-7.2:** API documentation via OpenAPI 3.1 spec, hosted on `/docs`.

**FR-7.3:** Webhooks for:

- `link.placed` — new backlink placed to your site
- `link.removed` — a link to your site was removed
- `link.replaced` — auto-replacement triggered
- `domain.vetted` — domain vetting completed
- `credits.low` — credit balance below threshold

---

## 4. Pricing

| Feature           | Free             | Starter ($29/mo) | Pro ($79/mo)        | Agency ($199/mo)             |
| ----------------- | ---------------- | ---------------- | ------------------- | ---------------------------- |
| Connected domains | 5                | 25               | 100                 | Unlimited                    |
| MCP requests/hour | 100              | 1,000            | 5,000               | Unlimited                    |
| Matching          | Basic (category) | Semantic         | Semantic + audience | Semantic + audience + custom |
| Link architecture | A-B-C            | A-B-C            | A-B-C + multi-hop   | Custom topologies            |
| DR tier matching  | Up to DR 40      | Up to DR 60      | Up to DR 80         | Unlimited                    |
| Link survival SLA | None             | 60 days          | 90 days             | 120 days + replacement       |
| Dashboard         | Basic            | Full             | Full + exports      | Full + white-label           |
| API access        | Read-only        | Full             | Full                | Full + bulk ops              |
| Support           | Community        | Email            | Priority email      | Dedicated Slack              |
| Credit bonus      | —                | +10%/mo          | +25%/mo             | +50%/mo                      |

Annual billing: 20% discount.

---

## 5. Non-Functional Requirements

**NFR-1:** API response time < 200ms (p95) for all read operations, < 500ms for matching.

**NFR-2:** MCP server response time < 1s for `weave_discover_links` with up to 10 results.

**NFR-3:** System availability: 99.9% uptime SLA.

**NFR-4:** Link validator processes entire network within 24-hour window.

**NFR-5:** Data retention: all link placement data retained for 2 years minimum.

**NFR-6:** GDPR compliant: user data exportable and deletable on request.

**NFR-7:** SOC 2 Type II compliance target for Year 2.

**NFR-8:** Horizontal scalability: architecture must support 100K+ domains without redesign.

---

## 6. Success Metrics

| Metric                         | 3 months | 6 months | 12 months |
| ------------------------------ | -------- | -------- | --------- |
| Registered domains             | 500      | 2,000    | 10,000    |
| Monthly active MCP connections | 200      | 1,000    | 5,000     |
| Links placed/month             | 2,000    | 15,000   | 100,000   |
| Paying customers               | 50       | 250      | 1,500     |
| MRR                            | $3,000   | $20,000  | $120,000  |
| Link survival rate (90-day)    | > 85%    | > 90%    | > 95%     |
| Avg match quality score        | > 60     | > 70     | > 75      |

---

## 7. Risks & Mitigations

| Risk                                     | Impact   | Mitigation                                                                                          |
| ---------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| Google penalizes link exchange networks  | Critical | A-B-C+ architecture, semantic relevance focus, natural anchor text variation, no footprint patterns |
| Low network liquidity (not enough sites) | High     | Generous free tier, seed the network with owned/partnered sites, content marketing                  |
| Spam/PBN infiltration                    | High     | Continuous automated vetting, community reporting, WTS decay on violations                          |
| MCP protocol changes                     | Medium   | Abstract MCP layer, support multiple protocol versions                                              |
| Competitor copies features               | Medium   | Move fast, build community, focus on DX superiority                                                 |

---

## 8. Roadmap

### Phase 1 — MVP (Weeks 1-6)

- User auth + domain registration + verification
- Basic domain vetting (DR, spam score, age)
- Category-based matching (upgrade to embeddings in Phase 2)
- Credit system with transparent formula
- MCP server with `discover_links` and `place_link`
- Basic dashboard (domain list, credit balance, link log)
- Landing page + docs

### Phase 2 — Intelligence (Weeks 7-10)

- Embedding-based semantic matching engine
- A-B-C triangulation algorithm
- Link validator/crawler (24h cycle)
- Full dashboard with analytics
- REST API + webhook system
- Auto-replacement SLA logic

### Phase 3 — Scale (Weeks 11-14)

- Multi-hop link architectures
- Audience overlap signals
- White-label dashboard for agencies
- Bulk operations API
- Advanced reporting + CSV/PDF export
- Community reporting system

### Phase 4 — Growth (Ongoing)

- Marketplace integrations (n8n, Make, Zapier)
- Chrome extension for manual link discovery
- Link building recommendations engine
- Partner program / affiliate system
- SOC 2 compliance work
