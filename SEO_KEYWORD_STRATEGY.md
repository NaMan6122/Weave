# Weave — SEO Keyword Strategy & Content Clusters

**Version:** 1.0
**Date:** 2026-07-15
**Status:** Approved

---

## 1. Primary Keywords (High Volume, High Intent)

| Keyword | Monthly Volume (est.) | Difficulty | Target Page | Intent |
|---------|----------------------|------------|-------------|--------|
| AI link building | 2,400 | Medium | Home, Features | Commercial |
| MCP link building | 320 | Low | Home, Docs, `/integrations/mcp` | Informational/Commercial |
| automated backlink exchange | 590 | Medium | Home, Pricing | Commercial |
| backlink exchange platform | 880 | Medium | Home, Comparison | Commercial |
| contextual link building AI | 210 | Low | Features, Blog | Informational |
| link building for AI content | 480 | Low | Blog, Use Cases | Informational/Commercial |

---

## 2. Secondary Keywords (Long-tail, Conversion-Focused)

| Keyword | Volume | Intent | Target Page |
|---------|--------|--------|-------------|
| how to get backlinks with AI | 320 | Informational | Blog, Docs |
| MCP server for SEO | 180 | Informational | `/docs/mcp-setup`, `/integrations` |
| credit-based link exchange | 140 | Commercial | Pricing, How it Works |
| A-B-C link building | 90 | Informational | Features, Blog |
| semantic backlink matching | 70 | Informational | Features, Blog |
| link building without outreach | 210 | Commercial | Home, Comparison |
| Weave vs Hrefmatch | 50 | Navigational | `/compare/hrefmatch` |
| best AI link building tool 2024 | 180 | Commercial | Blog, Review Pages |

---

## 3. Competitor Comparison Keywords

| Keyword | Target Page | Notes |
|---------|-------------|-------|
| Weave vs Hrefmatch | `/compare/hrefmatch` | Primary competitor |
| Weave vs manual outreach | `/compare/manual-outreach` | High intent |
| Weave vs link building agencies | `/compare/agencies` | Agency persona |
| Weave vs guest posting | `/compare/guest-posting` | Common alternative |
| Weave vs niche edits | `/compare/niche-edits` | Black-hat alternative |
| Weave vs Link Whisper | `/compare/link-whisper` | Internal linking tool |

---

## 4. Technical/Developer Keywords

| Keyword | Target Page | Audience |
|---------|-------------|----------|
| MCP server installation | `/docs/mcp-setup` | Developers |
| link building API | `/docs/api-reference` | Developers |
| backlink automation workflow | `/integrations` | Technical marketers |
| n8n link building | `/integrations/n8n` | Automation users |
| cursor MCP SEO | `/docs/mcp-setup` | AI-assisted developers |
| Weave MCP tools | `/docs/mcp-tools` | MCP users |

---

## 5. Content Cluster Architecture (Hub & Spoke)

### Cluster 1: AI Link Building Guide (Primary Hub)
**Hub:** `/blog/ai-link-building-guide` — "Complete Guide to AI-Powered Link Building in 2024"
- **Spokes:**
  - `/blog/semantic-link-matching-explained` — How embeddings find relevant partners
  - `/blog/triangulation-link-building` — A-B-C vs direct reciprocal links
  - `/blog/credit-based-link-economy` — Transparent credit system
  - `/blog/link-survival-sla-explained` — 90-day guarantee & auto-replacement
  - `/blog/domain-vetting-checklist` — DR, spam, PBN, age requirements

### Cluster 2: MCP for SEO Workflows (Developer Hub)
**Hub:** `/blog/mcp-seo-workflows` — "MCP for SEO: Automating Link Building with AI Agents"
- **Spokes:**
  - `/blog/cursor-mcp-link-building` — Cursor + Weave setup
  - `/blog/claude-mcp-backlinks` — Claude Desktop + Weave
  - `/blog/n8n-weave-automation` — n8n workflow templates
  - `/blog/make-com-weave-integration` — Make.com scenarios
  - `/blog/custom-mcp-workflows` — Building your own MCP tools

### Cluster 3: Backlink Exchange vs Outreach (Comparison Hub)
**Hub:** `/blog/backlink-exchange-vs-outreach` — "Why Link Exchanges Beat Manual Outreach in 2024"
- **Spokes:**
  - `/blog/link-exchange-cost-comparison` — $0 vs $100-500/link
  - `/blog/link-quality-exchange-vs-outreach` — Semantic relevance metrics
  - `/blog/link-speed-exchange-vs-outreach` — Same day vs 2-4 weeks
  - `/blog/link-risk-exchange-vs-outreach` — SLA vs no guarantee
  - `/blog/link-scaling-exchange-vs-outreach` — Unlimited vs agency bottleneck

---

## 6. Landing Page Optimization

### Home Page (`/`)
- **Primary:** AI link building, MCP link building, automated backlink exchange
- **Secondary:** contextual link building AI, link building for AI content
- **H1:** "AI-Native Backlink Exchange for Automated Link Building"
- **Meta Title:** "Weave — AI-Native Backlink Exchange | MCP-Powered Link Building"
- **Meta Description:** "Automatically discover, place, and earn contextual backlinks through your AI agent. No manual outreach, no opaque pricing. Try free."

### Features Page (`/#features`)
- **Primary:** semantic matching, credit system, A-B-C triangulation, MCP integration
- **Sections:** Each feature = H2 with keyword-rich description

### Pricing Page (`/#pricing`)
- **Primary:** credit-based link exchange, backlink exchange platform
- **Table:** Plan names match keyword modifiers (Free, Starter, Pro, Agency)

### Comparison Page (`/compare/hrefmatch`)
- **Primary:** Weave vs Hrefmatch
- **Schema:** `ProductComparison` structured data

---

## 7. Structured Data (Schema.org)

### Home Page
```json
{
  "@type": "SoftwareApplication",
  "name": "Weave",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Cloud",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  },
  "featureList": [
    "Semantic link matching",
    "Credit-based exchange",
    "A-B-C triangulation",
    "MCP integration",
    "Link health monitoring"
  ]
}
```

### Comparison Pages
```json
{
  "@type": "ProductComparison",
  "name": "Weave vs Hrefmatch",
  "comparedProducts": [
    { "@type": "Product", "name": "Weave", "url": "https://getweave.io" },
    { "@type": "Product", "name": "Hrefmatch", "url": "https://hrefmatch.com" }
  ],
  "comparisonCriteria": [
    "Matching quality",
    "Link architecture",
    "Pricing transparency",
    "Automation level",
    "Link monitoring"
  ]
}
```

### Blog Posts
```json
{
  "@type": "BlogPosting",
  "headline": "Complete Guide to AI-Powered Link Building in 2024",
  "author": { "@type": "Organization", "name": "Weave" },
  "publisher": { "@type": "Organization", "name": "Weave" },
  "datePublished": "2026-07-15",
  "dateModified": "2026-07-15",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://getweave.io/blog/ai-link-building-guide" }
}
```

---

## 8. Internal Linking Matrix

| From Page | To Page | Anchor Text | Priority |
|-----------|---------|-------------|----------|
| Home | `/blog/ai-link-building-guide` | "Complete guide to AI link building" | High |
| Home | `/blog/mcp-seo-workflows` | "MCP for SEO workflows" | High |
| Home | `/compare/hrefmatch` | "Weave vs Hrefmatch" | Medium |
| Features | `/blog/semantic-link-matching-explained` | "How semantic matching works" | High |
| Features | `/blog/triangulation-link-building` | "A-B-C triangulation explained" | High |
| Pricing | `/blog/credit-based-link-economy` | "How the credit system works" | Medium |
| `/blog/ai-link-building-guide` | `/blog/semantic-link-matching-explained` | "Semantic matching deep dive" | High |
| `/blog/ai-link-building-guide` | `/blog/triangulation-link-building` | "A-B-C triangulation" | High |
| `/blog/mcp-seo-workflows` | `/docs/mcp-setup` | "MCP setup guide" | High |
| `/compare/hrefmatch` | `/pricing` | "View transparent pricing" | Medium |

---

## 9. Technical SEO Checklist

- [ ] XML sitemap with all cluster pages
- [ ] Robots.txt allows all content
- [ ] Canonical URLs on all pages
- [ ] Hreflang (en only for MVP)
- [ ] Core Web Vitals: LCP < 2.5s, INP < 200ms, CLS < 0.1
- [ ] Structured data validates in Rich Results Test
- [ ] Page speed: < 3s total load time
- [ ] Mobile-first responsive design
- [ ] HTTPS everywhere
- [ ] No index bloat (thin content pages)

---

## 10. Measurement & KPIs

| Metric | 3 Month Target | 6 Month Target | 12 Month Target |
|--------|----------------|----------------|-----------------|
| Organic traffic | 5,000/mo | 20,000/mo | 80,000/mo |
| Keyword rankings (top 10) | 15 | 50 | 150 |
| Blog conversion rate | 1.5% | 2.5% | 3.5% |
| Comparison page CTR | 8% | 12% | 15% |
| Backlinks to blog | 50 | 200 | 800 |

---

## 11. Out of Scope (Phase 2+)

- International SEO (non-English)
- Video SEO (YouTube embeds)
- Podcast SEO
- Local SEO (not applicable)
- E-commerce schema (not applicable)