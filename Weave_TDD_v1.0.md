







TECHNICAL DESIGN DOCUMENT

weave

AI-Native Backlink Exchange Platform









Confidential — Internal Use Only



# 1. Document Overview

This Technical Design Document (TDD) provides the full engineering specification for weave. It is the primary reference for the development agent and covers system architecture, data models, API contracts, algorithm implementations, infrastructure decisions, and testing strategy.

This document maps directly to the weave PRD v1.0. Every P0 feature defined in the PRD has a corresponding technical specification in this document.



# 2. Technology Stack



# 3. System Architecture

## 3.1 Component Diagram

The system has four primary runtime components communicating over HTTPS and internal service calls:





## 3.2 Request Flow — get_backlink

The critical path from agent tool call to match response:

AI Agent calls MCP tool get_backlink with article text and domain.

MCP Server (TypeScript) validates API key via Redis cache, then POSTs to Python Backend API /api/v1/match.

Backend API: generates embedding for article_text using bge-small-en-v1.5 (sentence-transformers).

pgvector ANN query retrieves top-50 candidate articles by cosine similarity.

Scoring service re-ranks top-50 by full match_score formula, returns top-3.

Anchor text generated for top match via Claude Haiku call (async — non-blocking for response).

Response: [{url, anchor_text, partner_dr, match_score, article_title}] returned to agent.

Total P50 target: < 400ms. Embedding: ~50ms. ANN query: ~30ms. Scoring: ~10ms. Network: ~100ms.



## 3.3 Async Flow — Link Health Crawl

BullMQ cron job triggers every Sunday 02:00 UTC.

Job fetches all active link placements from PostgreSQL (status = 'live').

For each placement: Playwright headless browser loads the partner article URL.

Checks: is the anchor link present in the DOM? Is href unchanged? Is page returning 200?

On failure: updates placement status, deducts partner credits (penalty × 2), restores your credits.

Sends failure notification via Resend email + in-dashboard notification.

Three failures in 90 days: partner domain flagged, moved to manual review queue.



# 4. Database Schema

## 4.1 PostgreSQL + pgvector Schema



### 4.1.1 domains

CREATE TABLE domains (

  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  domain        TEXT NOT NULL UNIQUE,

  dr            INTEGER DEFAULT 0,

  monthly_traffic INTEGER DEFAULT 0,

  spam_score    FLOAT DEFAULT 0,

  niche_tags    TEXT[] DEFAULT '{}',

  language      TEXT DEFAULT 'en',

  status        TEXT DEFAULT 'pending',  -- pending | active | suspended | rejected

  credit_balance BIGINT DEFAULT 500,

  link_health_score FLOAT DEFAULT 1.0,

  verified_at   TIMESTAMPTZ,

  created_at    TIMESTAMPTZ DEFAULT NOW(),

  updated_at    TIMESTAMPTZ DEFAULT NOW()

);

CREATE INDEX idx_domains_status ON domains(status);

CREATE INDEX idx_domains_dr ON domains(dr);



### 4.1.2 articles

CREATE TABLE articles (

  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  domain_id     UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,

  url           TEXT NOT NULL UNIQUE,

  title         TEXT,

  content_hash  TEXT,  -- SHA256 of content — detect updates

  embedding     vector(384),  -- bge-small-en-v1.5 output

  niche_tags    TEXT[],

  word_count    INTEGER,

  monthly_traffic INTEGER DEFAULT 0,

  published_at  TIMESTAMPTZ,

  last_crawled_at TIMESTAMPTZ,

  created_at    TIMESTAMPTZ DEFAULT NOW()

);

CREATE INDEX idx_articles_domain ON articles(domain_id);

CREATE INDEX idx_articles_embedding ON articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);



### 4.1.3 link_placements

CREATE TABLE link_placements (

  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  source_article_id UUID NOT NULL REFERENCES articles(id),  -- article containing the link

  target_article_id UUID NOT NULL REFERENCES articles(id),  -- article being linked to

  anchor_text      TEXT NOT NULL,

  credits_debited  INTEGER NOT NULL,

  credits_earned   INTEGER NOT NULL,

  status           TEXT DEFAULT 'pending', -- pending | live | failed | removed

  health_checked_at TIMESTAMPTZ,

  failure_count    INTEGER DEFAULT 0,

  placed_at        TIMESTAMPTZ DEFAULT NOW(),

  removed_at       TIMESTAMPTZ,

  routing_type     TEXT DEFAULT 'direct',  -- direct | abc

  UNIQUE(source_article_id, target_article_id)

);

CREATE INDEX idx_placements_status ON link_placements(status);

CREATE INDEX idx_placements_source ON link_placements(source_article_id);



### 4.1.4 credit_ledger

CREATE TABLE credit_ledger (

  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  domain_id   UUID NOT NULL REFERENCES domains(id),

  amount      BIGINT NOT NULL,  -- positive = credit, negative = debit

  type        TEXT NOT NULL,    -- earned | spent | clawback | bonus | penalty | top_up

  placement_id UUID REFERENCES link_placements(id),

  note        TEXT,

  created_at  TIMESTAMPTZ DEFAULT NOW()

);

CREATE INDEX idx_ledger_domain ON credit_ledger(domain_id);

CREATE INDEX idx_ledger_type ON credit_ledger(type);



### 4.1.5 vetting_queue

CREATE TABLE vetting_queue (

  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  domain_id   UUID NOT NULL REFERENCES domains(id),

  auto_checks JSONB,   -- { dr, traffic, spam_score, domain_age, pbn_detected }

  status      TEXT DEFAULT 'pending',  -- pending | approved | rejected | manual_review

  reviewer_note TEXT,

  created_at  TIMESTAMPTZ DEFAULT NOW(),

  reviewed_at TIMESTAMPTZ

);



# 5. API Contracts

## 5.1 MCP Server Tools (TypeScript)



### 5.1.1 get_backlink

Request

// POST https://api.weave.io/mcp/tools/get_backlink

{

  "article_text": "Full article content as plain text string (max 50,000 chars)",

  "domain": "yourdomain.com",

  "niche": "fitness"  // optional — improves recall speed, not used for scoring

}



Response

// 200 OK

{

  "matches": [

    {

      "url": "https://partner.com/article-slug",

      "article_title": "10 Best Protein Sources for Vegans",

      "anchor_text": "plant-based protein sources",  // LLM-generated

      "anchor_alternatives": ["vegan protein options", "protein for plant-based diets"],

      "partner_dr": 42,

      "match_score": 0.847,

      "score_breakdown": {

        "semantic_similarity": 0.91,

        "dr_proximity": 0.82,

        "traffic_freshness": 0.74

      }

    }

  ],

  "credits_required": 170,  // cost to place on top match

  "your_credit_balance": 4200

}



### 5.1.2 place_link

Request

// POST https://api.weave.io/mcp/tools/place_link

{

  "your_url": "https://yourdomain.com/your-article",

  "partner_url": "https://partner.com/article-slug",

  "anchor": "plant-based protein sources",

  "domain": "yourdomain.com"

}



Response

// 200 OK

{

  "placement_id": "uuid-v4",

  "credits_debited": 170,

  "credits_earned": 104,  // queued for when reciprocal link is placed

  "credit_balance": 4030,

  "status": "pending",  // pending until health check confirms link is live

  "estimated_reciprocal_placement": "within 72 hours"

}



### 5.1.3 check_credits

// GET https://api.weave.io/mcp/tools/check_credits?domain=yourdomain.com

{

  "domain": "yourdomain.com",

  "credit_balance": 4030,

  "domain_rating": 21,

  "placements_made": 14,

  "backlinks_received": 11,

  "link_health_score": 0.92,  // fraction of your placed links currently live

  "tier": "paid"

}



### 5.1.4 browse_network

// GET https://api.weave.io/mcp/tools/browse_network

// Query params: niche, min_dr, max_dr, language, min_traffic, page, page_size (max 50)

{

  "sites": [

    {

      "domain": "str***ng.com",  // partially masked for privacy

      "niche": "fitness",

      "sub_niche": "strength training",

      "dr": 23,

      "monthly_traffic": 18000,

      "language": "en",

      "domain_age_months": 14,

      "link_health_score": 0.97

    }

  ],

  "total": 72,

  "page": 1,

  "page_size": 20

}



## 5.2 Backend REST API (Python / FastAPI)

Internal API consumed by the MCP Server and Dashboard. All endpoints are authenticated. Base URL: https://api-internal.weave.io/api/v1





# 6. Core Algorithm Implementations

## 6.1 Embedding Pipeline

### 6.1.1 Model Setup (Python)

# app/services/embedder.py

from sentence_transformers import SentenceTransformer

import numpy as np



# Load once at startup — ~90MB model

model = SentenceTransformer("BAAI/bge-small-en-v1.5")



def embed_article(text: str) -> list[float]:

    # Truncate to 512 tokens (model max)

    text = text[:8000]

    # BGE models use a query prefix for retrieval

    prefixed = f"Represent this document for retrieval: {text}"

    embedding = model.encode(prefixed, normalize_embeddings=True)

    return embedding.tolist()  # 384-dim float list



def embed_query(query_text: str) -> list[float]:

    prefixed = f"Represent this query for retrieval: {query_text}"

    embedding = model.encode(prefixed, normalize_embeddings=True)

    return embedding.tolist()



### 6.1.2 pgvector ANN Query

# app/services/matcher.py

async def find_candidates(embedding: list[float], exclude_domain: str, limit: int = 50) -> list[dict]:

    query = """

        SELECT

            a.id, a.url, a.title, a.monthly_traffic, a.published_at,

            d.domain, d.dr,

            1 - (a.embedding <=> $1::vector) AS semantic_similarity

        FROM articles a

        JOIN domains d ON d.id = a.domain_id

        WHERE d.domain != $2

          AND d.status = 'active'

          AND a.embedding IS NOT NULL

        ORDER BY a.embedding <=> $1::vector

        LIMIT $3

    """

    rows = await db.fetch(query, embedding, exclude_domain, limit)

    return [dict(r) for r in rows]



## 6.2 Match Scoring

# app/services/scorer.py

import math

from datetime import datetime, timezone



def dr_proximity_score(your_dr: int, partner_dr: int) -> float:

    """Penalises extreme DR mismatches. Returns 0–1."""

    return 1.0 - abs(your_dr - partner_dr) / 100.0



def traffic_freshness_score(monthly_traffic: int, published_at: datetime, max_traffic: int = 500000) -> float:

    """Log-normalised traffic score with recency decay."""

    if monthly_traffic <= 0:

        return 0.0

    traffic_score = math.log10(monthly_traffic + 1) / math.log10(max_traffic + 1)

    # Recency: articles > 18 months old with stagnant traffic get 0.5x weight

    age_months = (datetime.now(timezone.utc) - published_at).days / 30

    recency_weight = 0.5 if age_months > 18 else 1.0

    return min(traffic_score * recency_weight, 1.0)



def compute_match_score(semantic_sim: float, your_dr: int, partner_dr: int,

                        monthly_traffic: int, published_at: datetime) -> float:

    dr_score = dr_proximity_score(your_dr, partner_dr)

    tf_score = traffic_freshness_score(monthly_traffic, published_at)

    return (0.60 * semantic_sim) + (0.25 * dr_score) + (0.15 * tf_score)



def rank_candidates(candidates: list[dict], your_dr: int) -> list[dict]:

    for c in candidates:

        c["match_score"] = compute_match_score(

            c["semantic_similarity"], your_dr,

            c["dr"], c["monthly_traffic"], c["published_at"]

        )

    return sorted(candidates, key=lambda x: x["match_score"], reverse=True)[:3]



## 6.3 Credit Economy

# app/services/credits.py

import math



def credit_value(dr: int) -> int:

    """DR-weighted credit value per link placement."""

    return max(1, int(math.log10(max(dr, 1) + 1) * 100))



async def process_placement(

    placing_domain_id: str,

    partner_dr: int,

    your_dr: int,

    placement_id: str,

    db,

) -> dict:

    cost = credit_value(partner_dr)   # cost to have your link on their site

    earn = credit_value(your_dr)      # credits earned when they link to you



    # Debit the placing domain immediately

    await db.execute("""

        UPDATE domains SET credit_balance = credit_balance - $1 WHERE id = $2

    """, cost, placing_domain_id)



    # Credit earned goes to ledger — released when reciprocal is confirmed live

    await db.execute("""

        INSERT INTO credit_ledger(domain_id, amount, type, placement_id, note)

        VALUES ($1, $2, 'spent', $3, 'Placement cost')

    """, placing_domain_id, -cost, placement_id)



    return {"credits_debited": cost, "credits_earned_pending": earn}



## 6.4 Anchor Text Generation

# app/services/anchor.py

import anthropic



client = anthropic.AsyncAnthropic()



async def generate_anchors(

    source_snippet: str,  # 200-word excerpt from source article around insertion point

    target_title: str,

    target_snippet: str,  # 200-word excerpt from target article

) -> list[str]:

    prompt = f"""Generate 3 natural anchor text phrases for a hyperlink.



    Source context (where the link will appear):

    {source_snippet}



    Target article being linked to: "{target_title}"

    Target article summary: {target_snippet}



    Requirements:

    - 2 to 5 words each

    - Must flow naturally in the source context

    - Should relate to the target article topic

    - No generic phrases like 'click here' or 'read more'



    Return ONLY a JSON array of 3 strings. Example: ["phrase one", "phrase two", "phrase three"]"""



    response = await client.messages.create(

        model="claude-haiku-4-5-20251001",

        max_tokens=100,

        messages=[{"role": "user", "content": prompt}]

    )



    import json

    anchors = json.loads(response.content[0].text)

    return anchors[:3]



## 6.5 Link Health Crawler

# app/workers/health_crawler.py

from playwright.async_api import async_playwright

from urllib.parse import urlparse



async def check_link_health(source_url: str, target_url: str, anchor_text: str) -> dict:

    """Returns {live: bool, reason: str}"""

    async with async_playwright() as p:

        browser = await p.chromium.launch()

        page = await browser.new_page()

        try:

            await page.goto(source_url, timeout=15000, wait_until="domcontentloaded")

            # Find anchor matching target URL

            link = await page.query_selector(f'a[href*="{urlparse(target_url).path}"]')

            if not link:

                return {"live": False, "reason": "link_not_found"}

            href = await link.get_attribute("href")

            text = (await link.inner_text()).strip().lower()

            if anchor_text.lower() not in text and text not in anchor_text.lower():

                return {"live": True, "reason": "anchor_changed", "found_anchor": text}

            return {"live": True, "reason": "ok"}

        except Exception as e:

            return {"live": False, "reason": f"error: {str(e)}"}

        finally:

            await browser.close()



# 7. MCP Server Implementation

## 7.1 Project Structure

mcp-server/

├── src/

│   ├── index.ts          # MCP server entry — registers all tools

│   ├── tools/

│   │   ├── getBacklink.ts

│   │   ├── placeLink.ts

│   │   ├── checkCredits.ts

│   │   └── browseNetwork.ts

│   ├── auth.ts           # API key validation via Redis

│   ├── client.ts         # HTTP client to Python backend

│   └── types.ts          # Shared TypeScript interfaces

├── package.json

└── tsconfig.json



## 7.2 Tool Registration (index.ts)

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import { getBacklink } from "./tools/getBacklink.js";

import { placeLink } from "./tools/placeLink.js";

import { checkCredits } from "./tools/checkCredits.js";

import { browseNetwork } from "./tools/browseNetwork.js";



const server = new McpServer({ name: "weave", version: "1.0.0" });



server.tool("get_backlink",

  "Find a high-quality backlink match for the current article being written. Call this when writing content to automatically embed a relevant partner link.",

  { article_text: { type: "string", description: "Full article text (plain text, max 50000 chars)" },

    domain: { type: "string", description: "Your domain (e.g. yourdomain.com)" },

    niche: { type: "string", description: "Optional niche hint (e.g. fitness, finance, tech)" } },

  getBacklink

);



server.tool("place_link",

  "Record a link placement after embedding the partner link in your article. Deducts credits.",

  { your_url: { type: "string" }, partner_url: { type: "string" },

    anchor: { type: "string" }, domain: { type: "string" } },

  placeLink

);



## 7.3 API Key Auth (auth.ts)

import { createClient } from "@upstash/redis";



const redis = createClient({ url: process.env.UPSTASH_URL!, token: process.env.UPSTASH_TOKEN! });



export async function validateApiKey(key: string): Promise<{ valid: boolean; domainId?: string }> {

  // Cache positive hits for 5 minutes to reduce DB load

  const cached = await redis.get<string>(`apikey:${key}`);

  if (cached) return { valid: true, domainId: cached };



  const res = await fetch(`${process.env.BACKEND_URL}/api/v1/auth/validate`, {

    method: "POST",

    headers: { "Content-Type": "application/json", "X-Internal-Key": process.env.INTERNAL_KEY! },

    body: JSON.stringify({ api_key: key })

  });

  const data = await res.json();

  if (data.valid) {

    await redis.setex(`apikey:${key}`, 300, data.domain_id);  // 5-min TTL

    return { valid: true, domainId: data.domain_id };

  }

  return { valid: false };

}



# 8. Dashboard — Next.js App Router

## 8.1 Route Structure

app/

├── (marketing)/          # Public pages — /, /pricing, /docs

│   ├── page.tsx          # Landing page

│   └── pricing/page.tsx

├── (app)/                # Authenticated — layout wraps with sidebar

│   ├── layout.tsx        # Auth guard + sidebar nav

│   ├── dashboard/page.tsx # DR graph, credit balance, recent placements

│   ├── domains/page.tsx  # Add/remove domains, vetting status

│   ├── backlinks/page.tsx # Full placement log with health status

│   ├── network/page.tsx  # Browse member sites

│   └── settings/page.tsx # API key, billing, notifications

├── api/

│   ├── auth/[...nextauth]/route.ts

│   ├── domains/route.ts  # POST: add domain

│   ├── placements/route.ts

│   └── stripe/webhook/route.ts



## 8.2 Key Dashboard Components

DomainSelector — sidebar dropdown for switching between user's domains.

DRHistoryChart — Recharts LineChart rendering weekly DR snapshots from domain_dr_history table.

BacklinkTable — paginated table with columns: partner site (masked), anchor text, DR, status badge, placed date. Status badge: live (green), pending (amber), failed (red).

CreditLedger — filterable table of all credit transactions with running balance.

NetworkBrowser — filterable card grid of member sites. Filters: niche (multi-select), DR range (slider), language, min traffic.

HealthScoreRing — SVG ring chart per domain showing fraction of links currently live.



# 9. Infrastructure & DevOps

## 9.1 Environment Variables



## 9.2 Railway Services

Three Railway services, each from the same monorepo with separate start commands:

weave-api: uvicorn app.main:app --host 0.0.0.0 --port 8000 — Python backend

weave-worker: python -m app.worker — BullMQ consumer for crawl + embedding jobs

weave-mcp: node dist/index.js — TypeScript MCP server

All three share environment variables via Railway project-level env vars. Auto-deploy from main branch.



## 9.3 Supabase Setup Checklist

Enable pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;

Run schema migrations in order: domains, articles, link_placements, credit_ledger, vetting_queue.

Enable Row Level Security on all tables. Domains: user_id = auth.uid(). Others: join via domain ownership.

Create IVFFlat index on articles.embedding after first 1,000 articles are inserted (index degrades at low cardinality).

Set up Supabase Edge Functions for Stripe webhook if direct Railway webhook becomes unreliable.



# 10. Testing Strategy

## 10.1 Test Pyramid



## 10.2 Critical Unit Tests

### Scoring Formula (pytest)

def test_match_score_weights_semantic_highest():

    score = compute_match_score(

        semantic_sim=1.0, your_dr=50, partner_dr=50,

        monthly_traffic=10000, published_at=datetime.now(timezone.utc)

    )

    assert 0 <= score <= 1



def test_dr_proximity_penalises_mismatch():

    assert dr_proximity_score(10, 90) < dr_proximity_score(10, 15)



def test_credit_value_logarithmic():

    assert credit_value(10) < credit_value(50) < credit_value(90)

    assert credit_value(0) >= 1



## 10.3 Integration Test — get_backlink Flow

# tests/integration/test_match.py

async def test_get_backlink_returns_matches(test_client, seeded_articles):

    # Seed: 10 fitness articles from partner domains in pgvector

    response = await test_client.post("/api/v1/match", json={

        "article_text": "Guide to plant-based protein for muscle building...",

        "domain": "test-domain.com",

        "your_dr": 25

    }, headers={"X-API-Key": "test-key"})

    assert response.status_code == 200

    data = response.json()

    assert len(data["matches"]) <= 3

    assert all(0 <= m["match_score"] <= 1 for m in data["matches"])

    # Top match should be fitness-related

    assert any("protein" in m["article_title"].lower() for m in data["matches"])



# 11. Security Considerations

## 11.1 API Security

All API keys are stored as bcrypt hashes. Plain key is shown once at generation, never stored.

Rate limiting: 100 req/min per API key (sliding window via Upstash Redis). Exceeded = 429.

Internal API between MCP server and Python backend uses a separate INTERNAL_KEY not exposed to users.

All POST bodies validated with Pydantic (Python) and Zod (TypeScript). Invalid = 422.



## 11.2 Credit Fraud Prevention

Anomalous credit accumulation detector: domain earning > 3x median credits/week triggers manual review flag.

Article URL ownership verification: domains can only submit articles from their own domain. Checked via HEAD request to verify the domain returns a matching HTML canonical.

Link placement idempotency: UNIQUE constraint on (source_article_id, target_article_id) prevents double-billing.



## 11.3 Data Privacy

Member domains are partially masked in browse_network responses (str***ng.com style) to prevent cold scraping.

Full domain revealed only when a placement is confirmed — requires a live link from both sides.

GDPR: user data deletion cascades from auth.users. Article embeddings deleted within 30 days of domain removal.



# 12. Open Questions for MVP





End of TDD — weave v1.0

This document is intended to be consumed directly by a development agent. All code samples are production-ready starting points, not pseudocode.