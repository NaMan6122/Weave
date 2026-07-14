import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.models.link import Link, Triangle


class TriangulationService:

    @staticmethod
    async def form_triangle(
        db: AsyncSession,
        domain_a_id: uuid.UUID,
        domain_b_id: uuid.UUID,
    ) -> Triangle | None:
        """
        Given A wants to link to B, find C such that:
        - B can link to C (compatible niche, DR within ±30)
        - C can link back to A (compatible niche, DR within ±30)
        - All three have different owners
        - No existing triangle contains all three domains
        """
        # Load A and B
        result = await db.execute(select(Domain).where(Domain.id == domain_a_id))
        domain_a = result.scalar_one_or_none()
        if domain_a is None:
            return None

        result = await db.execute(select(Domain).where(Domain.id == domain_b_id))
        domain_b = result.scalar_one_or_none()
        if domain_b is None:
            return None

        # Find candidate C domains: active, approved, different owner from A and B
        stmt = select(Domain).where(
            Domain.id != domain_a_id,
            Domain.id != domain_b_id,
            Domain.status == "active",
            Domain.vetting_status == "approved",
            Domain.user_id != domain_a.user_id,
            Domain.user_id != domain_b.user_id,
        )
        result = await db.execute(stmt)
        candidates = list(result.scalars().all())

        for candidate_c in candidates:
            # Check B -> C compatibility
            if not _is_compatible(domain_b, candidate_c):
                continue
            # Check C -> A compatibility
            if not _is_compatible(candidate_c, domain_a):
                continue

            # Check no existing triangle with all three
            existing = await db.execute(
                select(Triangle).where(
                    or_(
                        and_(
                            Triangle.domain_a_id == domain_a_id,
                            Triangle.domain_b_id == domain_b_id,
                            Triangle.domain_c_id == candidate_c.id,
                        ),
                        and_(
                            Triangle.domain_a_id == domain_a_id,
                            Triangle.domain_b_id == candidate_c.id,
                            Triangle.domain_c_id == domain_b_id,
                        ),
                        and_(
                            Triangle.domain_a_id == domain_b_id,
                            Triangle.domain_b_id == domain_a_id,
                            Triangle.domain_c_id == candidate_c.id,
                        ),
                        and_(
                            Triangle.domain_a_id == domain_b_id,
                            Triangle.domain_b_id == candidate_c.id,
                            Triangle.domain_c_id == domain_a_id,
                        ),
                        and_(
                            Triangle.domain_a_id == candidate_c.id,
                            Triangle.domain_b_id == domain_a_id,
                            Triangle.domain_c_id == domain_b_id,
                        ),
                        and_(
                            Triangle.domain_a_id == candidate_c.id,
                            Triangle.domain_b_id == domain_b_id,
                            Triangle.domain_c_id == domain_a_id,
                        ),
                    )
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            # Valid C found — create Triangle
            triangle = Triangle(
                domain_a_id=domain_a_id,
                domain_b_id=domain_b_id,
                domain_c_id=candidate_c.id,
                status="forming",
            )
            db.add(triangle)
            await db.flush()
            return triangle

        return None

    @staticmethod
    async def complete_triangle(db: AsyncSession, triangle_id: uuid.UUID) -> bool:
        """Check if all 3 link slots are filled; if so, mark complete."""
        result = await db.execute(
            select(Triangle).where(Triangle.id == triangle_id)
        )
        triangle = result.scalar_one_or_none()
        if triangle is None:
            return False

        if (
            triangle.link_ab_id is not None
            and triangle.link_bc_id is not None
            and triangle.link_ca_id is not None
        ):
            triangle.status = "complete"
            await db.flush()
            return True
        return False

    @staticmethod
    async def check_triangle_health(
        db: AsyncSession, triangle_id: uuid.UUID
    ) -> str:
        """Check status of all 3 links; mark triangle broken if any link is removed/broken."""
        result = await db.execute(
            select(Triangle).where(Triangle.id == triangle_id)
        )
        triangle = result.scalar_one_or_none()
        if triangle is None:
            return "not_found"

        link_ids = [
            triangle.link_ab_id,
            triangle.link_bc_id,
            triangle.link_ca_id,
        ]
        active_ids = [lid for lid in link_ids if lid is not None]

        if active_ids:
            result = await db.execute(
                select(Link).where(Link.id.in_(active_ids))
            )
            links = list(result.scalars().all())

            for link in links:
                if link.status in ("removed", "broken"):
                    triangle.status = "broken"
                    await db.flush()
                    return triangle.status

        return triangle.status

    @staticmethod
    async def assign_link_to_triangle(
        db: AsyncSession,
        link_id: uuid.UUID,
        triangle_id: uuid.UUID,
        position: str,
    ) -> None:
        """Assign a link to a triangle slot (ab, bc, or ca) and check completion."""
        result = await db.execute(
            select(Triangle).where(Triangle.id == triangle_id)
        )
        triangle = result.scalar_one_or_none()
        if triangle is None:
            raise ValueError(f"Triangle {triangle_id} not found")

        if position == "ab":
            triangle.link_ab_id = link_id
        elif position == "bc":
            triangle.link_bc_id = link_id
        elif position == "ca":
            triangle.link_ca_id = link_id
        else:
            raise ValueError(f"Invalid position: {position}")

        # Update the link's triangle_id
        result = await db.execute(select(Link).where(Link.id == link_id))
        link = result.scalar_one_or_none()
        if link is not None:
            link.triangle_id = triangle_id

        await db.flush()

        # Check if triangle is now complete
        await TriangulationService.complete_triangle(db, triangle_id)

    @staticmethod
    async def find_pending_triangles(
        db: AsyncSession, domain_id: uuid.UUID
    ) -> list[Triangle]:
        """Find forming triangles involving this domain that have missing links."""
        stmt = select(Triangle).where(
            Triangle.status == "forming",
            or_(
                Triangle.domain_a_id == domain_id,
                Triangle.domain_b_id == domain_id,
                Triangle.domain_c_id == domain_id,
            ),
            or_(
                Triangle.link_ab_id.is_(None),
                Triangle.link_bc_id.is_(None),
                Triangle.link_ca_id.is_(None),
            ),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


def _is_compatible(source: Domain, target: Domain) -> bool:
    """Check niche compatibility and DR range between two domains."""
    # Niche check: same niche, or both have a niche with matching first word
    source_niche = (source.niche or "").lower().strip()
    target_niche = (target.niche or "").lower().strip()

    if source_niche and target_niche:
        if source_niche != target_niche:
            # Allow if first word matches (e.g. "tech saas" and "tech marketing")
            if source_niche.split()[0] != target_niche.split()[0]:
                return False
    elif source.niche_strict or getattr(target, "niche_strict", False):
        # If either requires strict niche and the other has no niche, skip
        return False

    # DR range check: within ±30
    source_dr = source.dr or 0.0
    target_dr = target.dr or 0.0
    if abs(source_dr - target_dr) > 30:
        return False

    return True
