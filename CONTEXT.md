# Weave — Project Context & Decision Log

## What is Weave?

An AI-native backlink exchange platform. Website owners join a vetted network, and AI agents (via MCP) or the dashboard discover and place contextually relevant backlinks between member sites. Credits are exchanged instead of money — you earn credits by hosting links, spend them to get links placed on partner sites.

## Architecture

```
apps/api/          — Python FastAPI backend (async, SQLAlchemy, pgvector)
apps/web/          — Next.js 14 dashboard (App Router, Tailwind, shadcn/ui)
packages/mcp-server/ — TypeScript MCP server (stdio transport)
```

- **Database:** PostgreSQL + pgvector (384-dim embeddings)
- **Embeddings:** OpenAI `text-embedding-3-small` (384 dims via `dimensions` param), hash-projection fallback when no API key
- **Workers:** APScheduler — crawl, SLA, triangle, expiry, metrics, digest
- **Email:** Resend API
- **Payments:** DoDo Payments (stubs only — graceful 503 when keys not set)

## Key Design Decisions

| Decision                 | Choice                                                               | Why                                                                           |
| ------------------------ | -------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Credit formula           | `max(1, int(log10(max(dr,1)+1) * 100))`                              | PRD v1.0 spec — logarithmic scaling rewards quality without runaway inflation |
| Match scoring weights    | 60% semantic / 25% DR proximity / 15% traffic freshness              | PRD spec — semantic relevance dominates                                       |
| Domain verification      | DNS TXT only (`_weave.<domain>` → `weave-verify=<token>`)            | Simplest for automated agents; meta + file methods kept as fallbacks          |
| Vetting thresholds       | DR>=5, traffic>=500/mo, spam<15%, age>=6mo, no PBN                   | PRD quality gates                                                             |
| WTS (Weave Trust Score)  | DA*0.30 + content*0.25 + traffic*0.20 + link_profile*0.15 + age*0.10 | Composite quality signal, minimum 30 to pass                                  |
| Penalty for link removal | `credit_value(their_dr) * 2`                                         | PRD spec — strong deterrent against bad actors                                |
| Three-strikes rule       | 3 failures in 90 days → domain suspended                             | PRD trust enforcement                                                         |
| Embedding model          | OpenAI text-embedding-3-small                                        | Simpler deployment than local models, no GPU needed                           |
| Anchor text generation   | Claude Haiku via Anthropic API                                       | Cost-efficient, high-quality contextual anchors                               |
| Stripe                   | Deferred to Phase 2                                                  | Requires business verification; stubs wired up                                |

## External APIs Required

| Service         | Config Key                                    | Purpose                          |
| --------------- | --------------------------------------------- | -------------------------------- |
| OpenAI          | `OPENAI_API_KEY`                              | Embeddings for semantic matching |
| Anthropic       | `ANTHROPIC_API_KEY`                           | Anchor text generation (Haiku)   |
| Moz (free tier) | `MOZ_API_KEY`                                 | Domain Authority, spam score     |
| DataForSEO      | `DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD`    | Organic traffic, DR estimates    |
| Resend          | `RESEND_API_KEY`                              | Weekly digest emails             |
| DoDo Payments | `DODO_API_KEY` + `DODO_WEBHOOK_SECRET` | Payments (scaffolded)        |

## Seed Data

`scripts/seed.py` creates: 6 users, 50 domains (10 niches x 5), ~200 articles with embeddings, ~50 link placements. Domains distributed across users for realistic browse_network testing.

## Known Gaps / Future Work

- **DoDo Payments:** Scaffolded — 503 until keys are configured
- **A-B-C triangulation:** Service exists but not fully wired to PRD graph traversal spec
- **Webhooks:** Stubbed, not implemented
- **Real metrics API calls:** Moz/DataForSEO return empty when keys aren't set (graceful degradation)
- **Playwright crawler:** Deferred — using httpx for MVP, Playwright adds deployment complexity
