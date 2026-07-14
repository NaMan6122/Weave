# spec-004-v1 — Matching Engine (Category-Based MVP + Embedding Foundation)

**Version:** 1
**Date:** 2026-05-23
**Status:** Draft — pending human approval (Gate G1)
**PRD Refs:** FR-2.1, FR-2.2, FR-2.3, FR-2.4, FR-2.6
**TDD Refs:** §5.1 (Matching Engine), §3.2 (Vector Storage)

---

## 1. Overview

The matching engine is **implemented** in:
- `apps/api/app/services/matching.py` — discover_links, place_link, scoring
- `apps/api/app/services/embeddings.py` — text embedding via OpenAI/Anthropic
- `apps/api/app/models/page.py` — pgvector column for embeddings

**Current implementation:**
- Semantic similarity via pgvector embeddings (with niche-heuristic fallback)
- DR proximity scoring
- Traffic/freshness scoring
- Weights: 60% semantic, 25% DR proximity, 15% traffic/freshness
- Anchor text generation (natural, exact, branded)
- Exclusion rules: same owner, blocklist, language, niche_strict

**PRD specifies:** 40% semantic, 25% DR, 20% audience overlap, 10% freshness, 5% network diversity

**This spec fills gaps:**
- A. Scoring weight alignment (document deviation or adjust)
- B. Niche taxonomy for category fallback
- C. Audience overlap signal (deferred stub)
- D. Network diversity penalty
- E. Insertion hint generation
- F. Match quality display threshold

---

## 2. Scoring Weights

### 2.1 Current vs PRD

| Signal | Current | PRD | Recommendation |
|--------|---------|-----|----------------|
| Semantic relevance | 60% | 40% | Keep 50% — semantic is the strongest signal |
| DR proximity | 25% | 25% | Keep 25% |
| Audience overlap | 0% (not implemented) | 20% | Stub at 0%, add in Phase 2 |
| Freshness | 15% (combined with traffic) | 10% | Split: 10% freshness, 15% → 10% |
| Network diversity | 0% | 5% | Add 5% penalty for over-linking |

### 2.2 Proposed MVP Weights

```python
WEIGHTS = {
    "semantic": 0.50,
    "dr_proximity": 0.25,
    "freshness": 0.10,
    "audience_overlap": 0.10,  # stub: returns 0.5 for same niche, 0.2 otherwise
    "diversity": 0.05,
}
```

### 2.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-2.1 | Match score breakdown shows all 5 components |
| AC-2.2 | Weights sum to 1.0 |
| AC-2.3 | Match score total is between 0 and 1 (displayed as 0-100 to users) |

---

## 3. Niche Taxonomy (Category Fallback)

### 3.1 Purpose

When embeddings are unavailable (no API key, page not yet embedded), matching falls back to niche-based category similarity.

### 3.2 Taxonomy

Use a two-level taxonomy (category → subcategory):

```python
NICHE_TAXONOMY = {
    "technology": ["saas", "devtools", "ai-ml", "cybersecurity", "cloud", "mobile", "web-development"],
    "marketing": ["seo", "content-marketing", "social-media", "email-marketing", "ppc", "analytics"],
    "business": ["startup", "finance", "ecommerce", "consulting", "hr", "legal"],
    "health": ["fitness", "nutrition", "mental-health", "medical", "wellness"],
    "lifestyle": ["travel", "food", "fashion", "home", "parenting"],
    "education": ["online-learning", "coding-bootcamp", "academic", "languages"],
    "creative": ["design", "photography", "writing", "video", "music"],
}
```

### 3.3 Niche Similarity Scoring

```python
def niche_similarity(niche_a: str, niche_b: str) -> float:
    if niche_a == niche_b:
        return 1.0
    cat_a = get_parent_category(niche_a)
    cat_b = get_parent_category(niche_b)
    if cat_a == cat_b:
        return 0.6  # same category, different subcategory
    return 0.1  # different categories
```

### 3.4 When Fallback Triggers

- If source content has no embedding AND target page has no embedding
- `_semantic_similarity()` already has this fallback — refine it to use taxonomy

### 3.5 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-3.1 | Same niche → semantic score 1.0 in fallback mode |
| AC-3.2 | Same category, different subcategory → 0.6 |
| AC-3.3 | Different category → 0.1 |
| AC-3.4 | When embeddings available, taxonomy is not used |

---

## 4. Audience Overlap (Phase 2 Stub)

### 4.1 MVP Stub

For Phase 1, audience overlap returns a heuristic based on niche similarity and traffic tier proximity:

```python
def audience_overlap_stub(source_domain: Domain, target_domain: Domain) -> float:
    niche_sim = niche_similarity(source_domain.niche, target_domain.niche)
    traffic_sim = 1.0 - abs(
        log10(source_traffic + 1) - log10(target_traffic + 1)
    ) / 6.0  # normalized
    return (niche_sim * 0.7 + traffic_sim * 0.3)
```

### 4.2 Phase 2 (Documented for Future)

Real audience overlap via:
- Shared keyword rankings (SimilarWeb/Ahrefs API)
- Shared referring domains
- Topic co-occurrence in SERP results

### 4.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-4.1 | Audience overlap score returns 0-1 float |
| AC-4.2 | Same-niche domains with similar traffic get score > 0.7 |

---

## 5. Network Diversity Penalty

### 5.1 Purpose

Prevent over-linking to the same domain (creates footprint).

### 5.2 Formula

```python
def diversity_score(source_domain_id: UUID, target_domain_id: UUID, db) -> float:
    # Count existing links from source to target domain in last 90 days
    existing_count = count_links(source_domain_id, target_domain_id, days=90)
    if existing_count == 0:
        return 1.0
    elif existing_count == 1:
        return 0.7
    elif existing_count == 2:
        return 0.3
    else:
        return 0.0  # effectively excludes after 3 links
```

### 5.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-5.1 | First link to a domain gets diversity score 1.0 |
| AC-5.2 | 4th link to same domain in 90 days gets score 0.0 (filtered out) |
| AC-5.3 | After 90 days, counter resets |

---

## 6. Insertion Hint Generation

### 6.1 Current State

`insertion_hint` is always `None` in current implementation.

### 6.2 MVP Approach

Simple keyword-matching heuristic:

```python
def find_insertion_hint(content: str, target_title: str, target_niche: str) -> str | None:
    """Find the paragraph in content most relevant to the target."""
    paragraphs = content.split("\n\n")
    target_keywords = set(target_title.lower().split())

    best_paragraph = None
    best_overlap = 0

    for i, para in enumerate(paragraphs):
        para_words = set(para.lower().split())
        overlap = len(target_keywords & para_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_paragraph = i

    if best_paragraph is not None and best_overlap >= 2:
        snippet = paragraphs[best_paragraph][:80]
        return f"Consider linking near: \"{snippet}...\""
    return None
```

### 6.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-6.1 | Insertion hint returned when >2 keyword overlaps found |
| AC-6.2 | Hint includes snippet of the matching paragraph |
| AC-6.3 | Returns None when no good match found (not a random suggestion) |

---

## 7. Match Quality Display Threshold

### 7.1 Rule

Only return suggestions with `total_score >= 0.3` (30/100). Below this, the match is too weak to be useful.

### 7.2 Implementation

In `discover_links()`, after scoring and sorting:
```python
top = [s for s in scored if s[0] >= 0.3][:max_results]
```

### 7.3 Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-7.1 | No suggestions returned with score below 30 |
| AC-7.2 | If all candidates score below 30, return empty list |

---

## 8. Files to Modify

| File | Change |
|------|--------|
| `apps/api/app/services/matching.py` | Update weights, add diversity penalty, add insertion hint, add quality threshold, refine niche fallback |
| `apps/api/app/services/niche_taxonomy.py` | Create (taxonomy data + similarity function) |
| `apps/api/app/schemas/link.py` | Update MatchScoreBreakdown to include all 5 signals |

---

## 9. Out of Scope

- Full embedding-based semantic search via Pinecone (Phase 2)
- Real audience overlap via external APIs (Phase 2)
- Custom matching weight configuration per user
- A-B-C triangulation (separate spec-005)
