import math
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.models.link import Link
from app.models.page import Page
from app.schemas.link import (
    AnchorSuggestion,
    LinkSuggestion,
    MatchScoreBreakdown,
)
from app.services.credits import CreditService
from app.services.embeddings import EmbeddingService
from app.services.niche_taxonomy import niche_similarity
from app.services.notification import NotificationService

# Scoring weights (spec-004)
W_SEMANTIC = 0.50
W_DR = 0.25
W_FRESHNESS = 0.10
W_AUDIENCE = 0.10
W_DIVERSITY = 0.05

MIN_MATCH_SCORE = 0.30


def _semantic_similarity(source_embedding: list[float], page, source_niche: str, candidate_niche: str) -> float:
    """Cosine similarity normalised to 0-1. Falls back to niche taxonomy."""
    if page is not None and page.embedding is not None and source_embedding:
        sim = EmbeddingService.compute_similarity(source_embedding, list(page.embedding))
        return max(0.0, min(1.0, (sim + 1.0) / 2.0))
    return niche_similarity(source_niche, candidate_niche)


def _dr_proximity(your_dr: float, partner_dr: float) -> float:
    """1 - abs(your_dr - partner_dr) / 100, clamped to 0-1."""
    return max(0.0, 1.0 - abs(your_dr - partner_dr) / 100.0)


def _freshness_score(published_at: datetime | None) -> float:
    """Recency score: 1.0 for content <3 months, decaying to 0.3 for >18 months."""
    if not published_at:
        return 0.5
    age_months = (datetime.now(timezone.utc) - published_at).days / 30.0
    if age_months <= 3:
        return 1.0
    if age_months >= 18:
        return 0.3
    return 1.0 - (age_months - 3) * (0.7 / 15.0)


def _audience_overlap_stub(source_domain: Domain, target_domain: Domain) -> float:
    """Stub: niche similarity + traffic tier proximity (spec-004 §4)."""
    niche_sim = niche_similarity(source_domain.niche or "", target_domain.niche or "")
    source_traffic = source_domain.organic_traffic or 0
    target_traffic = target_domain.organic_traffic or 0
    if source_traffic <= 0 and target_traffic <= 0:
        return niche_sim
    traffic_sim = max(0.0, 1.0 - abs(
        math.log10(source_traffic + 1) - math.log10(target_traffic + 1)
    ) / 6.0)
    return niche_sim * 0.7 + traffic_sim * 0.3


async def _diversity_score(
    db: AsyncSession, source_domain_id: uuid.UUID, target_domain_id: uuid.UUID
) -> float:
    """Penalize over-linking to the same domain (spec-004 §5)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    result = await db.execute(
        select(func.count()).select_from(Link).where(
            Link.source_domain_id == source_domain_id,
            Link.target_domain_id == target_domain_id,
            Link.created_at >= cutoff,
        )
    )
    count = result.scalar_one()
    if count == 0:
        return 1.0
    if count == 1:
        return 0.7
    if count == 2:
        return 0.3
    return 0.0


def _compute_match_score(
    semantic: float, dr_prox: float, freshness: float, audience: float, diversity: float
) -> float:
    """Weighted composite score (spec-004 §2.2)."""
    return (
        W_SEMANTIC * semantic
        + W_DR * dr_prox
        + W_FRESHNESS * freshness
        + W_AUDIENCE * audience
        + W_DIVERSITY * diversity
    )


def _find_insertion_hint(content: str, target_title: str) -> str | None:
    """Find paragraph most relevant to the target for insertion hint (spec-004 §6)."""
    if not target_title or not content:
        return None
    paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
    target_keywords = {w.lower() for w in target_title.split() if len(w) > 3}
    if not target_keywords:
        return None

    best_para = None
    best_overlap = 0

    for para in paragraphs:
        para_words = {w.lower().strip(".,;:!?") for w in para.split()}
        overlap = len(target_keywords & para_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_para = para

    if best_para and best_overlap >= 2:
        snippet = best_para[:80]
        return f'Consider linking near: "{snippet}..."'
    return None


class MatchingService:

    @staticmethod
    async def discover_links(
        db: AsyncSession,
        content: str,
        source_url: str,
        source_domain_id: uuid.UUID,
        max_results: int = 5,
        niche_strict: bool = False,
        min_dr: float | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[LinkSuggestion]:
        result = await db.execute(
            select(Domain).where(Domain.id == source_domain_id)
        )
        source_domain = result.scalar_one_or_none()
        if source_domain is None:
            raise ValueError(f"Source domain {source_domain_id} not found")

        source_niche = source_domain.niche or ""
        source_dr = source_domain.dr or 0.0
        source_language = source_domain.language
        source_user_id = source_domain.user_id
        blocklist: list[str] = source_domain.blocklist or []

        conditions = [
            Page.domain_id != source_domain_id,
            Domain.status == "active",
            Domain.vetting_status == "approved",
            Domain.user_id != source_user_id,
        ]

        if source_language:
            conditions.append(Domain.language == source_language)
        if niche_strict:
            conditions.append(Domain.niche == source_niche)
        if min_dr is not None:
            conditions.append(Domain.dr >= min_dr)
        if exclude_domains:
            conditions.append(Domain.domain.notin_(exclude_domains))
        if blocklist:
            conditions.append(Domain.domain.notin_(blocklist))

        stmt = (
            select(Page, Domain)
            .join(Domain, Page.domain_id == Domain.id)
            .where(and_(*conditions))
        )
        result = await db.execute(stmt)
        candidates = result.all()

        source_embedding = await EmbeddingService.embed_text(content)

        scored: list[tuple[float, float, float, float, float, float, Page, Domain]] = []
        for page, domain in candidates:
            candidate_niche = domain.niche or ""
            candidate_dr = domain.dr or 0.0

            sem = _semantic_similarity(source_embedding, page, source_niche, candidate_niche)
            dr_p = _dr_proximity(source_dr, candidate_dr)
            fresh = _freshness_score(page.created_at)
            audience = _audience_overlap_stub(source_domain, domain)
            diversity = await _diversity_score(db, source_domain_id, domain.id)

            if diversity == 0.0:
                continue  # skip domains we've over-linked to

            total = _compute_match_score(sem, dr_p, fresh, audience, diversity)
            if total < MIN_MATCH_SCORE:
                continue

            scored.append((total, sem, dr_p, fresh, audience, diversity, page, domain))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_results]

        suggestions: list[LinkSuggestion] = []
        for total, sem, dr_p, fresh, audience, diversity, page, domain in top:
            title = page.title or ""
            title_words = title.split()
            domain_name = domain.domain.split(".")[0].capitalize()

            anchor_suggestions = [
                AnchorSuggestion(
                    type="natural",
                    text=" ".join(title_words[:5]) if title_words else domain.domain,
                ),
                AnchorSuggestion(type="exact", text=title or page.url),
                AnchorSuggestion(
                    type="branded",
                    text=f"{domain_name}'s {' '.join(title_words[:3])}"
                    if title_words
                    else domain_name,
                ),
            ]

            breakdown = MatchScoreBreakdown(
                semantic_similarity=round(sem, 4),
                dr_proximity=round(dr_p, 4),
                freshness=round(fresh, 4),
                audience_overlap=round(audience, 4),
                diversity=round(diversity, 4),
                total=round(total, 4),
            )

            insertion_hint = _find_insertion_hint(content, title)

            credits_earned = CreditService.calculate_credits_earned(
                source_dr, total * 100, "body"
            )

            suggestions.append(
                LinkSuggestion(
                    target_url=page.url,
                    target_title=page.title,
                    match_score=breakdown,
                    anchor_suggestions=anchor_suggestions,
                    insertion_hint=insertion_hint,
                    credits_earned=credits_earned,
                )
            )

        return suggestions

    @staticmethod
    async def index_page(
        db: AsyncSession,
        page_id: uuid.UUID,
        content: str,
    ) -> None:
        result = await db.execute(select(Page).where(Page.id == page_id))
        page = result.scalar_one_or_none()
        if page is None:
            raise ValueError(f"Page {page_id} not found")

        embedding = await EmbeddingService.embed_text(content)
        page.embedding = embedding
        await db.flush()

    @staticmethod
    async def place_link(
        db: AsyncSession,
        source_url: str,
        target_url: str,
        anchor_text: str,
        placement_type: str,
        source_domain_id: uuid.UUID,
    ) -> Link:
        result = await db.execute(
            select(Page).where(
                Page.url == source_url, Page.domain_id == source_domain_id
            )
        )
        source_page = result.scalar_one_or_none()
        if source_page is None:
            source_page = Page(
                domain_id=source_domain_id,
                url=source_url,
                status="active",
            )
            db.add(source_page)
            await db.flush()

        existing = await db.execute(
            select(Link).where(
                Link.source_page_id == source_page.id,
            ).join(Page, Link.target_page_id == Page.id).where(Page.url == target_url)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Link already exists between these URLs")

        result = await db.execute(select(Page).where(Page.url == target_url))
        target_page = result.scalar_one_or_none()
        if target_page is None:
            raise ValueError(f"Target page not found in network: {target_url}")

        result = await db.execute(
            select(Domain).where(Domain.id == target_page.domain_id)
        )
        target_domain = result.scalar_one()
        if target_domain.status != "active" or target_domain.vetting_status != "approved":
            raise ValueError("Target domain is not active/approved")

        result = await db.execute(
            select(Domain).where(Domain.id == source_domain_id)
        )
        source_domain = result.scalar_one()

        source_dr = source_domain.dr or 0.0
        target_dr = target_domain.dr or 0.0

        sem = _semantic_similarity([], None, source_domain.niche or "", target_domain.niche or "")
        dr_p = _dr_proximity(source_dr, target_dr)
        fresh = _freshness_score(target_page.created_at)
        audience = _audience_overlap_stub(source_domain, target_domain)
        diversity = await _diversity_score(db, source_domain_id, target_page.domain_id)
        total_score = _compute_match_score(sem, dr_p, fresh, audience, diversity)

        breakdown = {
            "semantic_similarity": round(sem, 4),
            "dr_proximity": round(dr_p, 4),
            "freshness": round(fresh, 4),
            "audience_overlap": round(audience, 4),
            "diversity": round(diversity, 4),
            "total": round(total_score, 4),
        }

        now = datetime.now(timezone.utc)
        credits_earned = CreditService.calculate_credits_earned(
            source_dr, total_score * 100, placement_type
        )

        link = Link(
            source_page_id=source_page.id,
            target_page_id=target_page.id,
            source_domain_id=source_domain_id,
            target_domain_id=target_page.domain_id,
            anchor_text=anchor_text,
            match_score=Decimal(str(round(total_score, 4))),
            match_breakdown=breakdown,
            placement_type=placement_type,
            credits_earned=credits_earned,
            status="placed",
            placed_at=now,
            sla_expires_at=now + timedelta(days=90),
        )
        db.add(link)
        await db.flush()

        await CreditService.earn_credits(
            db,
            source_domain_id,
            credits_earned,
            link.id,
            f"Link placed: {source_url} -> {target_url}",
        )

        # Auto-assign to pending triangle or form new one (spec-008)
        from app.services.triangulation import TriangulationService
        target_domain_id = target_page.domain_id
        pending = await TriangulationService.find_pending_triangles(db, source_domain_id)
        assigned = False
        for triangle in pending:
            if triangle.domain_a_id == source_domain_id and triangle.domain_b_id == target_domain_id and triangle.link_ab_id is None:
                await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "ab")
                assigned = True
                break
            elif triangle.domain_b_id == source_domain_id and triangle.domain_c_id == target_domain_id and triangle.link_bc_id is None:
                await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "bc")
                assigned = True
                break
            elif triangle.domain_c_id == source_domain_id and triangle.domain_a_id == target_domain_id and triangle.link_ca_id is None:
                await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "ca")
                assigned = True
                break

        # If no existing triangle matched, try to form a new one for A->B
        if not assigned:
            triangle = await TriangulationService.form_triangle(db, source_domain_id, target_domain_id)
            if triangle is not None:
                await TriangulationService.assign_link_to_triangle(db, link.id, triangle.id, "ab")

        await NotificationService.create(
            db,
            target_domain.user_id,
            "link_placed",
            "New backlink",
            f"{source_domain.domain} placed a backlink to {target_domain.domain}.",
            {"link_id": str(link.id), "source_domain": source_domain.domain},
        )

        return link

    @staticmethod
    async def get_link_health(
        db: AsyncSession,
        domain_id: uuid.UUID,
        status_filter: str = "all",
    ) -> list[Link]:
        conditions = [
            (Link.source_domain_id == domain_id)
            | (Link.target_domain_id == domain_id)
        ]
        if status_filter != "all":
            conditions.append(Link.status == status_filter)

        stmt = select(Link).where(and_(*conditions)).order_by(Link.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
