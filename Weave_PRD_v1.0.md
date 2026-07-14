







PRODUCT REQUIREMENTS DOCUMENT

weave

AI-Native Backlink Exchange Platform









Confidential — Internal Use Only



# 1. Executive Summary

weave is an AI-native backlink exchange platform that eliminates the bottleneck of manual SEO outreach. As AI tools accelerate content publishing velocity, link building has not kept pace. weave solves this by integrating directly into AI content workflows via the Model Context Protocol (MCP), enabling agents — Claude, Cursor, n8n, ChatGPT, and others — to discover, negotiate, and place high-quality contextual backlinks automatically at publish time.



Unlike existing link exchanges that match by niche tags and domain rating alone, weave performs deep semantic matching at the article level, enforces a DR-weighted credit economy, and actively monitors link health across the network — clawing back credits when links are removed.





# 2. Problem Statement

## 2.1 The AI Publishing Gap

Modern content teams using AI writing assistants can now publish 10–50x more content per month than teams relying on manual writing. However, backlink acquisition — a critical SEO signal — has not scaled with publishing velocity. The traditional outreach process involves:

Prospecting for relevant sites (2–4 hours per campaign)

Personalised outreach emails with low (~5%) acceptance rates

Payment of $150–$500+ per placement through agencies or marketplaces

No ongoing monitoring of whether placed links remain live



## 2.2 Existing Solutions Are Inadequate



# 3. Goals & Non-Goals

## 3.1 Goals

Enable any MCP-compatible AI agent to acquire contextual backlinks with zero manual outreach.

Deliver match quality measurably superior to tag-based systems via article-level semantic embeddings.

Enforce a fair credit economy with DR-weighted exchange rates and traffic freshness decay.

Actively monitor link health across the network and enforce SLA via automatic credit claw-back.

Onboard 100 verified sites in 90 days with pricing below all major competitors.



## 3.2 Non-Goals (MVP)

No browser extension — agent-first only.

No public marketplace for purchasing individual links with money — credits only.

No multi-language NLP matching in Phase 1 — English-only semantic model.

No white-label reseller tier in Phase 1.

No mobile app — web dashboard only.



# 4. User Personas

## 4.1 The AI-First Content Publisher (Primary)

Solo founder or small team publishing 20–200 AI-assisted articles per month.

Uses Claude, Cursor, or n8n for content workflows.

Understands SEO basics but lacks time or budget for traditional outreach.

Pain point: publishes great content that ranks poorly because they have no inbound links.

Goal: passive, compounding link acquisition that runs inside their existing workflow.



## 4.2 The SEO-Aware Developer (Secondary)

Developer running one or more content-heavy SaaS products or blogs.

Comfortable configuring MCP servers and reading API docs.

Wants programmatic control: credit balance checks, link placement triggers, DR monitoring.

Goal: integrate weave into a custom publishing pipeline, not just Claude Desktop.



## 4.3 The Growth-Stage Startup (Tertiary)

Marketing lead at a startup with multiple domains and content properties.

Needs domain authority growth to compete with established players.

Values the dashboard — wants reporting, placement logs, and weekly summaries.

Goal: demonstrable DR growth over 6–12 months with minimal headcount.



# 5. Feature Requirements



## 5.1 MCP Server & Agent Integration (P0)

### 5.1.1 Tool: get_backlink

Accepts full article text and optional niche hint. Returns top-3 matched partner articles with URL, suggested anchor text, and estimated DR. The agent embeds the returned link naturally in the article before publishing.

Input: { article_text: string, niche?: string, domain: string }

Output: { matches: [{ url, anchor_text, partner_dr, match_score, article_title }] }

P50 latency target: < 400ms

Requires authentication via API key passed in MCP server config



### 5.1.2 Tool: place_link

Called after the agent confirms a placement. Logs the exchange, deducts credits from the placing domain, and queues the reciprocal placement job.

Input: { your_url: string, partner_url: string, anchor: string, domain: string }

Output: { placement_id, credits_debited, credit_balance }

Idempotent — duplicate calls with same your_url + partner_url are no-ops



### 5.1.3 Tool: check_credits

Returns current credit balance, DR score, total placements made, and total backlinks received.



### 5.1.4 Tool: browse_network

Returns a filtered list of verified member sites. Filters: niche, min_dr, max_dr, language, min_traffic.



### 5.1.5 MCP Installation

One-line install via CLI:

claude mcp add weave https://api.weave.io/mcp

Compatible: Claude Desktop, Cursor, n8n, ChatGPT (MCP plugin), OpenClaw

Auth: API key injected as MCP server env variable



## 5.2 Semantic Matching Engine (P0)

The core algorithm that differentiates weave from all existing solutions.



### 5.2.1 Embedding Pipeline

On article publish, generate embedding using sentence-transformers (bge-small-en-v1.5 — 384-dim, fast, open source).

Store embedding in pgvector alongside article metadata (url, domain, dr, monthly_traffic, published_at, niche_tags).

Approximate nearest-neighbour search using IVFFlat index for sub-100ms retrieval at scale.



### 5.2.2 Match Scoring Formula

match_score = (0.60 × semantic_similarity) + (0.25 × DR_proximity) + (0.15 × traffic_freshness)

semantic_similarity: cosine similarity between article embeddings, normalised 0–1

DR_proximity: 1 - abs(your_dr - partner_dr) / 100 — penalises extreme DR mismatches

traffic_freshness: log10(monthly_traffic + 1) / log10(max_traffic + 1) × recency_weight — decays for articles older than 12 months with declining traffic



### 5.2.3 Anchor Text Generation

Pass the target article snippet + partner article title to an LLM call (Claude claude-haiku-4-5-20251001 for cost) to generate 3 candidate anchor phrases.

Rank candidates by: natural language fit, keyword relevance, length (2–5 words preferred).

Return top candidate as default; expose all 3 to dashboard users.



## 5.3 Credit Economy (P0)

### 5.3.1 Credit Valuation

Credits are valued logarithmically by domain rating to prevent high-DR domains from extracting value without contributing equivalently.

credit_value(dr) = log10(dr + 1) × 100

DR 10 domain: ~104 credits earned/spent per link

DR 50 domain: ~170 credits earned/spent per link

DR 90 domain: ~197 credits earned/spent per link



### 5.3.2 Exchange Rate Logic

Placing a link on a higher-DR site costs more credits than you earn from hosting their link.

cost_to_place = credit_value(partner_dr); credits_earned = credit_value(your_dr)

Net credit change = credits_earned - cost_to_place (can be negative — intentional by design)

Free tier starts with 500 bonus credits. Paid tier starts with 5,000 credits + monthly top-up.



### 5.3.3 Freshness Decay

Link placements in articles older than 12 months with declining month-over-month traffic earn 50% credits.

Reassessed quarterly. Domain owner notified with option to refresh article to restore full credit rate.



## 5.4 Link Health Monitor (P0)

The feature that makes the network trustworthy — and the biggest gap in all existing solutions.

Weekly crawler job (Playwright + httpx) checks every placed link: is the link present? Is the page indexed? Has the anchor changed? Is the page live?

If link is missing or noindexed: partner loses credits equal to credit_value(their_dr) × 2 (penalty multiplier). Your credits are restored.

Three strikes policy: partner domain is suspended from the network after 3 missed link SLAs in 90 days.

You receive email + dashboard notification within 24 hours of any link health failure.

Link health score displayed prominently in dashboard per domain.



## 5.5 Site Vetting Pipeline (P0)

### 5.5.1 Automated Checks

Minimum DR: 5 (Ahrefs API or open-source DR estimate)

Minimum organic traffic: 500 visits/month (Similarweb or DataForSEO)

Maximum spam score: < 15% (Moz API)

Domain age: minimum 6 months

PBN detection: cross-reference IP ranges, WHOIS patterns, and footprint analysis



### 5.5.2 Manual Review Queue

Sites that pass automated checks but have ambiguous signals go to a manual review queue (admin dashboard).

Solo MVP: founder reviews manually. Post-MVP: automated ML classifier trained on approved/rejected set.



## 5.6 Dashboard (P0)

Auth: email + password + magic link (NextAuth.js)

Domain management: add/remove domains, view per-domain DR history graph, credit balance

Backlink log: every received and placed link with partner site, DR, anchor text, date, health status

Network browser: explore member sites with filter/sort by niche, DR, traffic, language

Credit ledger: full transaction history — earned, spent, clawed-back

Weekly email digest: placements made, links received, credit movement, DR change



## 5.7 A-B-C Link Routing (P1)

Prevents direct reciprocal link patterns that are easily detected by Google's link graph analysis. Site A links to Site C; Site C links to Site B; Site B links to Site A — forming a triangulated loop rather than a direct swap.

Routing graph computed weekly based on network membership and niche similarity.

Each site participates in multiple triangles. Routing is transparent to users — they see who received their link, even if it was triangulated.

Implementation: weighted graph traversal with topical continuity constraint (niche similarity must be maintained across all three hops).



## 5.8 API Access (P1)

Full REST API identical to MCP tools — for developers building custom pipelines.

API key management in dashboard.

Rate limits: free = 100 req/day, paid = 10,000 req/day.

OpenAPI 3.1 spec published at /api/docs.



# 6. Key User Stories



# 7. Pricing Model





# 8. Success Metrics



# 9. Constraints & Assumptions

## 9.1 Constraints

Solo developer — architecture must be buildable and operable by one person.

Zero infrastructure budget at launch — use managed services (Supabase, Railway, Vercel) to eliminate ops overhead.

Must not require any client-side JavaScript injection or browser plugin — MCP-first, agent-first.

Must comply with Google Webmaster Guidelines — no hidden links, no keyword stuffing, no cloaking.



## 9.2 Assumptions

MCP adoption continues to accelerate — Claude, Cursor, and n8n all maintain MCP support.

Sentence-transformer models (bge-small-en-v1.5) run adequately on a single Railway instance with 2GB RAM.

pgvector on Supabase is sufficient for the embedding store at MVP scale (< 100k articles).

Founding members accept that A-B-C routing is a Phase 1 feature, not available at launch day.



# 10. Risks & Mitigations



# 11. Phased Roadmap

## Phase 1 — MVP (Weeks 1–6)

PostgreSQL schema + pgvector setup (Supabase)

MCP server (TypeScript): get_backlink, place_link, check_credits, browse_network

Embedding pipeline (Python / FastAPI): article ingestion → bge-small-en embedding → pgvector

Basic match scoring (semantic + DR proximity only)

Credit ledger (flat rate, no DR weighting yet)

Next.js dashboard: auth, domain management, backlink log

Manual site vetting process

Stripe integration for Early Access tier



## Phase 2 — Quality Layer (Weeks 7–12)

DR-weighted credit economy

Traffic freshness decay in match scoring

Link health crawler (weekly jobs via Bull queue)

Anchor text LLM generation

Automated vetting pipeline (spam score, PBN detection)

Weekly email digest

REST API + OpenAPI spec



## Phase 3 — Growth (Weeks 13+)

A-B-C routing graph

Network analytics dashboard

Multi-language support (multilingual-e5 model)

Affiliate / referral program

Public launch pricing + marketing site





End of PRD — weave v1.0