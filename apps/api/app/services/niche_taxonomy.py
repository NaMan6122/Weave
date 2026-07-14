"""Niche taxonomy for category-based matching fallback."""

NICHE_TAXONOMY: dict[str, list[str]] = {
    "technology": ["saas", "devtools", "ai-ml", "cybersecurity", "cloud", "mobile", "web-development"],
    "marketing": ["seo", "content-marketing", "social-media", "email-marketing", "ppc", "analytics"],
    "business": ["startup", "finance", "ecommerce", "consulting", "hr", "legal"],
    "health": ["fitness", "nutrition", "mental-health", "medical", "wellness"],
    "lifestyle": ["travel", "food", "fashion", "home", "parenting"],
    "education": ["online-learning", "coding-bootcamp", "academic", "languages"],
    "creative": ["design", "photography", "writing", "video", "music"],
}

# Reverse lookup: subcategory -> parent category
_SUBCATEGORY_TO_CATEGORY: dict[str, str] = {}
for category, subcategories in NICHE_TAXONOMY.items():
    _SUBCATEGORY_TO_CATEGORY[category] = category
    for sub in subcategories:
        _SUBCATEGORY_TO_CATEGORY[sub] = category


def get_parent_category(niche: str) -> str | None:
    """Get the parent category for a niche string."""
    niche = niche.lower().strip()
    if niche in _SUBCATEGORY_TO_CATEGORY:
        return _SUBCATEGORY_TO_CATEGORY[niche]
    # Try first word match
    first_word = niche.split()[0] if niche else ""
    if first_word in _SUBCATEGORY_TO_CATEGORY:
        return _SUBCATEGORY_TO_CATEGORY[first_word]
    return None


def niche_similarity(niche_a: str, niche_b: str) -> float:
    """Score niche similarity: 1.0 exact, 0.6 same category, 0.1 different."""
    a = niche_a.lower().strip()
    b = niche_b.lower().strip()

    if not a or not b:
        return 0.3  # unknown niche gets neutral score

    if a == b:
        return 1.0

    cat_a = get_parent_category(a)
    cat_b = get_parent_category(b)

    if cat_a and cat_b and cat_a == cat_b:
        return 0.6

    return 0.1
