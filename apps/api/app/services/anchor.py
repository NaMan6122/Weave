"""Anchor text generation via Claude Haiku for cost-efficient, natural anchor phrases."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


async def generate_anchors(
    source_snippet: str,
    target_title: str,
    target_snippet: str,
) -> list[str]:
    """Generate 3 natural anchor text phrases using Claude Haiku.

    Falls back to simple title-based anchors if API key is not configured.
    """
    api_key = getattr(settings, "anthropic_api_key", None)
    if not api_key:
        return _fallback_anchors(target_title)

    prompt = f"""Generate 3 natural anchor text phrases for a hyperlink.

Source context (where the link will appear):
{source_snippet[:500]}

Target article being linked to: "{target_title}"
Target article summary: {target_snippet[:500]}

Requirements:
- 2 to 5 words each
- Must flow naturally in the source context
- Should relate to the target article topic
- No generic phrases like 'click here' or 'read more'

Return ONLY a JSON array of 3 strings. Example: ["phrase one", "phrase two", "phrase three"]"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"]
            anchors = json.loads(text)
            return anchors[:3]
    except Exception as e:
        logger.warning("Anchor generation failed, using fallback: %s", e)
        return _fallback_anchors(target_title)


def _fallback_anchors(target_title: str) -> list[str]:
    """Simple title-based anchor generation when LLM is unavailable."""
    words = target_title.split()
    if len(words) >= 5:
        return [
            " ".join(words[:4]),
            " ".join(words[:3]),
            " ".join(words[1:4]),
        ]
    elif len(words) >= 2:
        return [target_title, " ".join(words[:2]), words[0]]
    else:
        return [target_title, target_title, target_title]
