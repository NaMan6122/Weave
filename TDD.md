# Weave — Technical Design Document (TDD)

**Version:** 1.0
**Date:** 2026-05-20
**Status:** Draft

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ AI Agent │  │ Web App  │  │ REST API │  │ Webhook Sink   │  │
│  │ (MCP)    │  │ (Next.js)│  │ Clients  │  │ (External)     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────▲────────┘  │
└───────┼──────────────┼──────────────┼───────────────┼───────────┘
        │              │              │               │
┌───────▼──────────────▼──────────────▼───────────────┼───────────┐
│                    API GATEWAY (Nginx / Cloudflare)              │
│                    Rate Limiting · Auth · TLS                    │
└───────┬──────────────┬──────────────┬───────────────┼───────────┘
        │              │              │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌────▼─────┐ ┌──────┴──────┐
│  MCP Server  │ │  Next.js   │ │ REST API │ │  Webhook    │
│  (TS/Node)   │ │  App       │ │ (FastAPI)│ │  Dispatcher │
│              │ │  (SSR+API) │ │          │ │  (Worker)   │
└───────┬──────┘ └─────┬──────┘ └────┬─────┘ └──────┬──────┘
        │              │              │               │
┌───────▼──────────────▼──────────────▼───────────────▼───────────┐
│                     SERVICE LAYER                                │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Matching │ │  Credit   │ │  Domain  │ │  Link Validator   │  │
│  │ Engine   │ │  Service  │ │  Vetting │ │  (Crawler)        │  │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘ └───────┬───────────┘  │
└───────┼──────────────┼──────────────┼──────────────┼────────────┘
        │              │              │              │
┌───────▼──────────────▼──────────────▼──────────────▼────────────┐
│                     DATA LAYER                                   │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │PostgreSQL│ │  Redis    │ │  Vector  │ │  Object Storage  │  │
│  │ (Neon)   │ │ (Upstash) │ │  DB      │ │  (S3/R2)         │  │
│  │          │ │           │ │(Pinecone)│ │                   │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 15 (App Router) + Tailwind CSS + shadcn/ui | SSR for landing/SEO, RSC for dashboard, excellent DX |
| **API (Web)** | Next.js Route Handlers | Co-located with frontend, handles auth flows, dashboard APIs |
| **API (Core)** | FastAPI (Python 3.12+) | ML/embedding pipeline, matching engine, domain vetting — Python ecosystem is stronger here |
| **MCP Server** | TypeScript + `@modelcontextprotocol/sdk` | Must be Node/TS per MCP spec, separate deployable |
| **Database** | PostgreSQL 16 (Neon) | Relational data, ACID transactions for credits, serverless scaling |
| **Cache/Queue** | Redis (Upstash) + BullMQ | Job queues (vetting, crawling, webhooks), caching, rate limiting |
| **Vector DB** | Pinecone (or pgvector for MVP) | Content embeddings for semantic matching |
| **Embeddings** | `all-MiniLM-L6-v2` (Phase 1) → `text-embedding-3-large` (Phase 2) | Fast local inference for MVP, upgrade to OpenAI for accuracy |
| **Auth** | NextAuth.js v5 (Auth.js) | OAuth + credentials, session management, JWT |
| **Object Storage** | Cloudflare R2 | Crawl snapshots, reports, exports |
| **Hosting** | Vercel (Next.js) + Railway/Fly.io (FastAPI + workers) | Vercel for frontend edge, Railway for persistent services |
| **Monitoring** | Sentry + Axiom | Error tracking + structured logging |
| **CI/CD** | GitHub Actions | Test, lint, build, deploy pipeline |

---

## 3. Database Schema

### 3.1 Core Tables

```sql
-- Users & Authentication
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    name            TEXT,
    avatar_url      TEXT,
    plan            TEXT NOT NULL DEFAULT 'free'
                    CHECK (plan IN ('free', 'starter', 'pro', 'agency')),
    stripe_customer_id TEXT,
    api_key         TEXT UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Registered Domains
CREATE TABLE domains (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain          TEXT UNIQUE NOT NULL,       -- e.g. "example.com"
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    verification_method TEXT,                    -- 'dns' | 'meta' | 'file'
    verification_token TEXT NOT NULL,

    -- Vetting scores (updated periodically)
    wts             INT,                         -- Weave Trust Score 0-100
    dr              INT,                         -- Domain Rating
    da              INT,                         -- Domain Authority
    spam_score      DECIMAL(5,2),
    domain_age_days INT,
    organic_traffic INT,                         -- Monthly estimated
    content_quality DECIMAL(5,2),                -- AI-assessed 0-100
    is_pbn          BOOLEAN DEFAULT FALSE,
    vetted_at       TIMESTAMPTZ,
    vetting_status  TEXT NOT NULL DEFAULT 'pending'
                    CHECK (vetting_status IN ('pending', 'approved', 'rejected', 'suspended')),
    rejection_reason TEXT,

    -- Config
    niche           TEXT,                         -- Primary niche/category
    language        TEXT NOT NULL DEFAULT 'en',
    blocklist       TEXT[] DEFAULT '{}',          -- Domains to never match with
    niche_strict    BOOLEAN DEFAULT FALSE,

    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'suspended', 'removed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_domains_user ON domains(user_id);
CREATE INDEX idx_domains_niche ON domains(niche);
CREATE INDEX idx_domains_wts ON domains(wts);
CREATE INDEX idx_domains_status ON domains(status) WHERE status = 'active';

-- Pages/Articles (indexed for matching)
CREATE TABLE pages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id       UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    url             TEXT UNIQUE NOT NULL,
    title           TEXT,
    content_hash    TEXT,                         -- SHA256 of content for change detection
    niche           TEXT,
    language        TEXT NOT NULL DEFAULT 'en',
    word_count      INT,
    embedding_id    TEXT,                          -- Reference to vector DB entry
    last_crawled_at TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'removed', 'noindex')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pages_domain ON pages(domain_id);
CREATE INDEX idx_pages_url ON pages(url);

-- Credit Accounts (one per domain)
CREATE TABLE credit_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id       UUID UNIQUE NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    balance         DECIMAL(12,2) NOT NULL DEFAULT 0
                    CHECK (balance >= 0),
    lifetime_earned DECIMAL(12,2) NOT NULL DEFAULT 0,
    lifetime_spent  DECIMAL(12,2) NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Credit Transactions (audit trail)
CREATE TABLE credit_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID NOT NULL REFERENCES credit_accounts(id),
    type            TEXT NOT NULL
                    CHECK (type IN ('earned', 'spent', 'reversed', 'bonus', 'expired')),
    amount          DECIMAL(12,2) NOT NULL,
    link_id         UUID REFERENCES links(id),    -- NULL for bonuses/expiry
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_credit_tx_account ON credit_transactions(account_id);
CREATE INDEX idx_credit_tx_created ON credit_transactions(created_at);

-- Links (the core exchange record)
CREATE TABLE links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Source (the page containing the outbound link)
    source_page_id  UUID NOT NULL REFERENCES pages(id),
    source_domain_id UUID NOT NULL REFERENCES domains(id),
    -- Target (the page being linked to)
    target_page_id  UUID NOT NULL REFERENCES pages(id),
    target_domain_id UUID NOT NULL REFERENCES domains(id),

    anchor_text     TEXT NOT NULL,
    match_score     DECIMAL(5,2),                 -- 0-100
    match_breakdown JSONB,                         -- { semantic, dr, audience, freshness, diversity }
    placement_type  TEXT NOT NULL DEFAULT 'body'
                    CHECK (placement_type IN ('body', 'sidebar', 'footer', 'author_bio')),

    -- Credit accounting
    credits_earned  DECIMAL(12,2),                 -- Credits earned by source
    credits_spent   DECIMAL(12,2),                 -- Credits spent by target

    -- Triangulation
    triangle_id     UUID REFERENCES triangles(id),

    -- Status tracking
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'placed', 'live', 'modified',
                                      'removed', 'broken', 'replaced', 'expired')),
    placed_at       TIMESTAMPTZ,
    verified_at     TIMESTAMPTZ,                   -- Last successful crawl verification
    removed_at      TIMESTAMPTZ,
    sla_expires_at  TIMESTAMPTZ,                   -- Link survival SLA deadline

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_links_source_domain ON links(source_domain_id);
CREATE INDEX idx_links_target_domain ON links(target_domain_id);
CREATE INDEX idx_links_status ON links(status);
CREATE INDEX idx_links_triangle ON links(triangle_id);

-- Triangles (A-B-C link structures)
CREATE TABLE triangles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_a_id     UUID NOT NULL REFERENCES domains(id),
    domain_b_id     UUID NOT NULL REFERENCES domains(id),
    domain_c_id     UUID NOT NULL REFERENCES domains(id),
    -- A links to B, B links to C, C links to A
    link_ab_id      UUID REFERENCES links(id),
    link_bc_id      UUID REFERENCES links(id),
    link_ca_id      UUID REFERENCES links(id),
    status          TEXT NOT NULL DEFAULT 'forming'
                    CHECK (status IN ('forming', 'complete', 'broken', 'dissolved')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Webhook Subscriptions
CREATE TABLE webhooks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    events          TEXT[] NOT NULL,                -- e.g. {'link.placed', 'link.removed'}
    secret          TEXT NOT NULL,                  -- HMAC signing secret
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Domain DR/WTS History (for trend charts)
CREATE TABLE domain_metrics_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id       UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    dr              INT,
    da              INT,
    wts             INT,
    organic_traffic INT,
    spam_score      DECIMAL(5,2),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_metrics_domain_date ON domain_metrics_history(domain_id, recorded_at);
```

### 3.2 Vector Storage

Content embeddings stored in Pinecone (or pgvector for MVP):

```
Namespace: "pages"
Vector dimensions: 384 (MiniLM) or 3072 (text-embedding-3-large)
Metadata per vector:
  - page_id: UUID
  - domain_id: UUID
  - niche: string
  - language: string
  - dr: int
  - wts: int
  - url: string
  - title: string
```

---

## 4. Service Architecture

### 4.1 MCP Server (`/packages/mcp-server`)

```
packages/mcp-server/
├── src/
│   ├── index.ts              # MCP server entrypoint
│   ├── tools/
│   │   ├── discover-links.ts # weave_discover_links tool
│   │   ├── place-link.ts     # weave_place_link tool
│   │   ├── check-balance.ts  # weave_check_balance tool
│   │   ├── domain-status.ts  # weave_domain_status tool
│   │   └── link-health.ts    # weave_link_health tool
│   ├── auth.ts               # API key validation
│   └── client.ts             # HTTP client to Core API
├── package.json
├── tsconfig.json
└── README.md
```

**MCP Registration Command:**
```bash
claude mcp add weave -- npx @weave/mcp-server --api-key YOUR_KEY
# or
claude mcp add weave https://mcp.getweave.io/sse --api-key YOUR_KEY
```

The MCP server is a thin client — all business logic lives in the Core API (FastAPI). The MCP server:
1. Receives tool calls from AI agents
2. Authenticates via API key
3. Proxies to Core API
4. Formats responses for MCP protocol

### 4.2 Core API (`/apps/api`)

FastAPI application handling all business logic.

```
apps/api/
├── app/
│   ├── main.py                # FastAPI app setup
│   ├── config.py              # Settings / env vars
│   ├── dependencies.py        # DI (db session, auth, etc.)
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── domain.py
│   │   ├── page.py
│   │   ├── link.py
│   │   ├── credit.py
│   │   └── triangle.py
│   ├── schemas/               # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py
│   │   ├── domains.py
│   │   ├── matching.py
│   │   ├── credits.py
│   │   ├── links.py
│   │   └── webhooks.py
│   ├── services/
│   │   ├── matching.py        # Matching engine
│   │   ├── vetting.py         # Domain vetting pipeline
│   │   ├── credits.py         # Credit calculations
│   │   ├── triangulation.py   # A-B-C formation
│   │   ├── embeddings.py      # Content embedding pipeline
│   │   └── crawler.py         # Link validator crawler
│   ├── workers/
│   │   ├── vetting_worker.py  # Async domain vetting jobs
│   │   ├── crawl_worker.py    # Link validation jobs
│   │   ├── metrics_worker.py  # DR/WTS refresh jobs
│   │   ├── expiry_worker.py   # Credit expiration jobs
│   │   └── webhook_worker.py  # Webhook dispatch
│   └── utils/
│       ├── security.py
│       └── rate_limit.py
├── tests/
├── pyproject.toml
└── Dockerfile
```

### 4.3 Web Application (`/apps/web`)

```
apps/web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    # Landing page
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (marketing)/
│   │   ├── pricing/page.tsx
│   │   ├── docs/page.tsx
│   │   └── blog/page.tsx
│   ├── dashboard/
│   │   ├── layout.tsx              # Dashboard shell + domain switcher
│   │   ├── page.tsx                # Overview
│   │   ├── domains/
│   │   │   ├── page.tsx            # Domain list
│   │   │   ├── [id]/page.tsx       # Domain detail
│   │   │   └── add/page.tsx        # Add domain flow
│   │   ├── links/page.tsx          # Link log
│   │   ├── credits/page.tsx        # Credit history
│   │   ├── analytics/page.tsx      # Charts + metrics
│   │   ├── settings/page.tsx       # Account settings
│   │   └── api-keys/page.tsx       # API key management
│   └── api/
│       ├── auth/[...nextauth]/route.ts
│       └── proxy/[...path]/route.ts  # Proxy to Core API
├── components/
│   ├── ui/                         # shadcn components
│   ├── dashboard/
│   │   ├── domain-switcher.tsx
│   │   ├── credit-balance.tsx
│   │   ├── link-table.tsx
│   │   ├── dr-chart.tsx
│   │   └── match-score-badge.tsx
│   └── marketing/
│       ├── hero.tsx
│       ├── pricing-table.tsx
│       └── feature-grid.tsx
├── lib/
│   ├── api-client.ts               # Typed API client
│   └── utils.ts
├── next.config.ts
├── tailwind.config.ts
└── package.json
```

---

## 5. Key Algorithms

### 5.1 Matching Engine

```python
# Simplified matching pipeline

async def discover_links(
    content: str,
    source_domain_id: UUID,
    max_results: int = 5,
    niche_strict: bool = False,
    min_dr: int | None = None,
    exclude_domains: list[str] | None = None,
) -> list[LinkSuggestion]:

    # 1. Embed the input content
    content_embedding = await embed(content)

    # 2. Query vector DB for semantically similar pages
    candidates = await vector_db.query(
        vector=content_embedding,
        top_k=max_results * 10,  # Over-fetch for filtering
        filter={
            "domain_id": {"$ne": str(source_domain_id)},
            "language": source_domain.language,
            **({"niche": source_domain.niche} if niche_strict else {}),
            **({"dr": {"$gte": min_dr}} if min_dr else {}),
        },
    )

    # 3. Score each candidate
    scored = []
    for candidate in candidates:
        if candidate.domain in (exclude_domains or []):
            continue
        if candidate.domain_id in get_same_owner_domains(source_domain_id):
            continue

        score = calculate_match_score(
            semantic=candidate.similarity_score,          # 40%
            dr_proximity=dr_proximity(source_dr, candidate.dr),  # 25%
            audience_overlap=await get_audience_overlap(
                source_domain_id, candidate.domain_id
            ),                                             # 20%
            freshness=freshness_score(candidate.created_at),  # 10%
            diversity=diversity_penalty(
                source_domain_id, candidate.domain_id
            ),                                             # 5%
        )
        scored.append((candidate, score))

    # 4. Sort by composite score, take top N
    scored.sort(key=lambda x: x[1].total, reverse=True)
    top = scored[:max_results]

    # 5. Generate anchor text suggestions for each
    suggestions = []
    for candidate, score in top:
        anchors = generate_anchor_texts(content, candidate.title, candidate.url)
        insertion = find_insertion_point(content, candidate)
        credits = calculate_credits_earned(source_domain, candidate, score)
        suggestions.append(LinkSuggestion(
            target_url=candidate.url,
            target_title=candidate.title,
            match_score=score,
            anchor_suggestions=anchors,
            insertion_point=insertion,
            credits_earned=credits,
        ))

    return suggestions
```

### 5.2 Triangulation Algorithm

```python
async def form_triangle(
    domain_a_id: UUID,
    domain_b_id: UUID,  # A wants to link to B
) -> Triangle | None:
    """
    Given A wants to link to B, find C such that:
    - B can link to C (semantic match exists)
    - C can link to A (semantic match exists)
    - No existing triangle contains all three
    - All three are different owners
    """

    # Find domains that B could link to
    b_candidates = await find_match_candidates(domain_b_id)

    for domain_c in b_candidates:
        # Check C can link back to A
        c_to_a_score = await check_match_feasibility(domain_c.id, domain_a_id)
        if c_to_a_score < MIN_TRIANGLE_MATCH_SCORE:
            continue

        # Verify no existing triangle with these three
        if await triangle_exists(domain_a_id, domain_b_id, domain_c.id):
            continue

        # Verify different owners
        owners = await get_owners([domain_a_id, domain_b_id, domain_c.id])
        if len(set(owners)) < 3:
            continue

        # Form the triangle
        triangle = await create_triangle(
            domain_a=domain_a_id,
            domain_b=domain_b_id,
            domain_c=domain_c.id,
        )
        return triangle

    return None  # No valid triangle found; queue for later
```

### 5.3 Credit Calculation

```python
def calculate_credits_earned(
    source_domain: Domain,
    target_candidate: Page,
    match_score: MatchScore,
    placement_type: str = "body",
) -> Decimal:
    BASE_CREDIT = Decimal("10")

    dr_multiplier = Decimal(str(source_domain.dr / 50))
    relevance_multiplier = Decimal(str(match_score.total / 100))
    placement_multiplier = {
        "body": Decimal("1.0"),
        "sidebar": Decimal("0.5"),
        "footer": Decimal("0.3"),
        "author_bio": Decimal("0.3"),
    }[placement_type]

    return (BASE_CREDIT * dr_multiplier * relevance_multiplier
            * placement_multiplier).quantize(Decimal("0.01"))


def calculate_credits_required(target_dr: int) -> Decimal:
    BASE_COST = Decimal("10")

    if target_dr <= 20:
        multiplier = Decimal("0.5")
    elif target_dr <= 40:
        multiplier = Decimal("1.0")
    elif target_dr <= 60:
        multiplier = Decimal("2.0")
    elif target_dr <= 80:
        multiplier = Decimal("4.0")
    else:
        multiplier = Decimal("8.0")

    return (BASE_COST * multiplier).quantize(Decimal("0.01"))
```

---

## 6. MCP Protocol Specification

### 6.1 Tool: `weave_discover_links`

```json
{
  "name": "weave_discover_links",
  "description": "Discover relevant backlink opportunities for your content. Returns ranked suggestions with anchor text and match scores.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "The article content or draft to find link opportunities for"
      },
      "url": {
        "type": "string",
        "description": "The URL where this content will be published"
      },
      "max_results": {
        "type": "integer",
        "default": 5,
        "description": "Maximum number of link suggestions (1-20)"
      },
      "niche_strict": {
        "type": "boolean",
        "default": false,
        "description": "Only match within the same niche"
      },
      "min_dr": {
        "type": "integer",
        "description": "Minimum Domain Rating of suggested targets"
      },
      "exclude_domains": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Domains to exclude from suggestions"
      }
    },
    "required": ["content", "url"]
  }
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "target_url": "https://example.com/article",
      "target_title": "Complete Guide to Container Orchestration",
      "match_score": {
        "total": 87,
        "semantic": 92,
        "dr_proximity": 85,
        "audience_overlap": 78,
        "freshness": 90,
        "diversity": 95
      },
      "anchor_suggestions": [
        { "type": "natural", "text": "container orchestration best practices" },
        { "type": "exact", "text": "container orchestration guide" },
        { "type": "branded", "text": "Example.com's orchestration guide" }
      ],
      "insertion_hint": "Consider linking in the paragraph about deployment strategies",
      "credits_earned": 12.4
    }
  ],
  "credit_balance": 156.80
}
```

### 6.2 Tool: `weave_place_link`

```json
{
  "name": "weave_place_link",
  "description": "Confirm placement of an outbound link and earn credits.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_url": {
        "type": "string",
        "description": "The URL of the page containing the outbound link"
      },
      "target_url": {
        "type": "string",
        "description": "The URL being linked to"
      },
      "anchor_text": {
        "type": "string",
        "description": "The anchor text used for the link"
      },
      "placement_type": {
        "type": "string",
        "enum": ["body", "sidebar", "footer", "author_bio"],
        "default": "body"
      }
    },
    "required": ["source_url", "target_url", "anchor_text"]
  }
}
```

---

## 7. Background Workers

| Worker | Schedule | Description |
|--------|----------|-------------|
| `vetting_worker` | On-demand (queue) | Processes new domain vetting: DR/DA lookup, spam check, PBN detection, content quality assessment |
| `crawl_worker` | Every 24h | Crawls all placed links to verify they're still live. Updates link status. |
| `metrics_worker` | Weekly | Refreshes DR/DA/traffic for all active domains. Records to history table. |
| `expiry_worker` | Daily | Expires credits older than 180 days. Sends warning at 150 days. |
| `webhook_worker` | On-demand (queue) | Dispatches webhook events with HMAC-signed payloads. Retries with exponential backoff (3 attempts). |
| `triangle_worker` | Hourly | Attempts to form triangles for queued link requests that couldn't be immediately triangulated. |
| `sla_worker` | Daily | Checks links approaching SLA expiry. Queues replacements for removed links. |

---

## 8. Authentication & Security

### 8.1 Auth Flows

```
Web App:
  User → NextAuth → OAuth Provider (Google/GitHub) → Session Cookie (httpOnly)

MCP Server:
  AI Agent → API Key (env var) → MCP Server → Core API (API Key in header)

REST API:
  Client → Bearer Token (JWT) or API Key → Core API
```

### 8.2 API Key Management

- Keys generated with `crypto.randomBytes(32).toString('hex')` → prefixed `wv_live_` / `wv_test_`
- Stored as SHA-256 hash in DB (never plaintext)
- Users can create multiple keys with labels
- Keys can be rotated/revoked from dashboard

### 8.3 Security Measures

- All endpoints rate-limited (per API key + IP)
- HMAC-SHA256 signed webhook payloads
- CSRF protection on web app
- Input sanitization on all user inputs (URLs, domains, anchor text)
- SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- Content Security Policy headers
- Domain verification prevents claiming domains you don't own

---

## 9. Deployment Architecture

```
Production:
├── Vercel
│   ├── Next.js App (Edge + Serverless)
│   └── API Routes (Serverless)
├── Railway / Fly.io
│   ├── FastAPI Core API (2+ instances, auto-scale)
│   ├── BullMQ Workers (dedicated instances per worker type)
│   └── MCP Server (SSE endpoint, auto-scale)
├── Neon
│   └── PostgreSQL (serverless, auto-scale)
├── Upstash
│   └── Redis (serverless)
├── Pinecone
│   └── Vector DB (serverless)
├── Cloudflare
│   ├── R2 (object storage)
│   ├── DNS
│   └── CDN + WAF
└── Stripe
    └── Billing & subscriptions
```

### 9.1 Environment Setup

```
# .env.example
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
PINECONE_API_KEY=...
PINECONE_INDEX=weave-pages

NEXTAUTH_SECRET=...
NEXTAUTH_URL=https://getweave.io

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

MOZ_API_KEY=...             # Domain metrics
DATAFORSEO_LOGIN=...        # Alternative domain metrics
DATAFORSEO_PASSWORD=...

OPENAI_API_KEY=...          # For text-embedding-3-large (Phase 2)

SENTRY_DSN=...
AXIOM_TOKEN=...
```

---

## 10. Testing Strategy

| Level | Tool | Coverage Target |
|-------|------|----------------|
| **Unit** | pytest (API), Vitest (MCP + Web) | Services, credit calculations, matching scoring — 90% |
| **Integration** | pytest + testcontainers | DB operations, queue processing, full matching pipeline — 80% |
| **API** | pytest + httpx | All endpoints, auth flows, rate limiting — 95% |
| **E2E** | Playwright | Critical user flows: register, add domain, view dashboard — core paths |
| **MCP** | Custom harness | All 5 tools with mock API responses |
| **Load** | k6 | Matching endpoint at 100 RPS, MCP at 50 concurrent |

---

## 11. Monorepo Structure

```
weave/
├── apps/
│   ├── web/                    # Next.js frontend + API routes
│   └── api/                    # FastAPI core backend
├── packages/
│   ├── mcp-server/             # MCP server (npm publishable)
│   ├── shared-types/           # Shared TypeScript types
│   └── db/                     # Drizzle schema + migrations (for Next.js side)
├── workers/                    # BullMQ worker definitions
├── infra/                      # Docker, Railway config, Terraform
├── docs/                       # API docs, architecture decision records
├── scripts/                    # Dev scripts, seed data
├── PRD.md
├── TDD.md
├── turbo.json                  # Turborepo config
├── pnpm-workspace.yaml
└── README.md
```

---

## 12. Phase 1 (MVP) Scope — Detailed

### What we build in Weeks 1-6:

**Week 1-2: Foundation**
- Monorepo setup (Turborepo + pnpm)
- PostgreSQL schema + migrations (Drizzle for TS, SQLAlchemy for Python)
- NextAuth setup (Google + GitHub OAuth)
- Basic landing page
- User registration + login flows

**Week 3-4: Core**
- Domain registration + verification (DNS/meta/file)
- Basic domain vetting (DR lookup via free APIs, spam score, age check)
- Credit system (earn/spend/balance with full transaction log)
- Category-based matching (no embeddings yet — simple niche + DR tier matching)
- MCP server with `discover_links` and `place_link` tools

**Week 5-6: Dashboard + Polish**
- Dashboard: domain list, credit balance, link log table
- Domain detail page with basic metrics
- API key generation
- MCP server documentation + setup guide
- Deployment pipeline (Vercel + Railway)
- Basic link validator (manual trigger, not yet automated)

### What we defer to Phase 2:
- Embedding-based matching
- A-B-C triangulation
- Automated 24h crawler
- Webhooks
- Analytics charts
- SLA/auto-replacement
- REST API (beyond what dashboard needs)
