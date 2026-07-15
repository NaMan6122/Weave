"""Domain registration, verification, and vetting service."""

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.credit import CreditAccount
from app.models.domain import Domain
from app.services.notification import NotificationService


class DomainService:
    """Handles domain lifecycle: registration, verification, and vetting."""

    # --- Create -----------------------------------------------------------

    @staticmethod
    async def create_domain(
        db: AsyncSession,
        user_id: str,
        domain_name: str,
        niche: str | None = None,
        language: str = "en",
    ) -> Domain:
        domain_name = domain_name.lower().strip()
        # Check uniqueness
        existing = await db.execute(
            select(Domain).where(Domain.domain == domain_name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Domain '{domain_name}' is already registered")

        token = uuid.uuid4().hex

        domain = Domain(
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            domain=domain_name,
            verification_token=token,
            niche=niche,
            language=language,
            status="pending",
            verified=False,
        )
        db.add(domain)
        await db.flush()  # get domain.id

        credit_account = CreditAccount(
            domain_id=domain.id,
            balance=Decimal("0.00"),
            lifetime_earned=Decimal("0.00"),
            lifetime_spent=Decimal("0.00"),
        )
        db.add(credit_account)
        await db.commit()
        await db.refresh(domain, attribute_names=["credit_account"])
        return domain

    # --- Verify -----------------------------------------------------------

    @staticmethod
    async def verify_domain(
        db: AsyncSession, domain_id: uuid.UUID, method: str
    ) -> Domain:
        domain = await db.get(Domain, domain_id)
        if not domain:
            raise LookupError("Domain not found")
        if domain.verified:
            return domain

        token = domain.verification_token
        verified = False

        if method == "dns":
            verified = await DomainService._verify_dns(domain.domain, token)
        elif method == "meta":
            verified = await DomainService._verify_meta(domain.domain, token)
        elif method == "file":
            verified = await DomainService._verify_file(domain.domain, token)
        else:
            raise ValueError(f"Unknown verification method: {method}")

        if not verified:
            raise ValueError(
                f"Verification failed via {method}. "
                f"Token '{token}' not found."
            )

        domain.verified = True
        domain.verification_method = method
        await db.commit()

        # Trigger vetting after successful verification
        await DomainService.vet_domain(db, domain.id)
        await db.refresh(domain)
        return domain

    @staticmethod
    async def _verify_dns(domain_name: str, token: str) -> bool:
        """Check DNS TXT record for domain verification.

        Tries dnspython first (direct DNS), falls back to Google DNS-over-HTTPS.
        Looks for TXT record: weave-verify=<token> on _weave.<domain>
        """
        expected = f"weave-verify={token}"

        # Try dnspython direct resolution first
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_weave.{domain_name}", "TXT")
            for rdata in answers:
                for txt_string in rdata.strings:
                    if txt_string.decode("utf-8").strip() == expected:
                        return True
        except Exception:
            pass

        # Fallback: Google DNS-over-HTTPS
        url = f"https://dns.google/resolve?name=_weave.{domain_name}&type=TXT"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                for answer in data.get("Answer", []):
                    txt = answer.get("data", "").strip('"')
                    if txt == expected:
                        return True
        except httpx.HTTPError:
            pass
        return False

    @staticmethod
    async def _verify_meta(domain_name: str, token: str) -> bool:
        """Fetch homepage and look for <meta name="weave-verify" content="{token}">."""
        url = f"https://{domain_name}"
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                pattern = (
                    r'<meta\s+name=["\']weave-verify["\']\s+'
                    r'content=["\']([^"\']+)["\']'
                )
                match = re.search(pattern, resp.text, re.IGNORECASE)
                if match and match.group(1) == token:
                    return True
        except httpx.HTTPError:
            pass
        return False

    @staticmethod
    async def _verify_file(domain_name: str, token: str) -> bool:
        """Fetch /.well-known/weave-verify.txt and compare to token."""
        url = f"https://{domain_name}/.well-known/weave-verify.txt"
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                if resp.text.strip() == token:
                    return True
        except httpx.HTTPError:
            pass
        return False

    # --- Vet --------------------------------------------------------------

    @staticmethod
    async def vet_domain(db: AsyncSession, domain_id: uuid.UUID) -> Domain:
        domain = await db.get(Domain, domain_id)
        if not domain:
            raise LookupError("Domain not found")

        # Fetch real metrics from external APIs if fields are empty
        from app.services.metrics import fetch_all_metrics
        if not domain.dr or not domain.organic_traffic:
            metrics = await fetch_all_metrics(domain.domain)
            if metrics.da and not domain.da:
                domain.da = metrics.da
            if metrics.dr and not domain.dr:
                domain.dr = metrics.dr
            if metrics.spam_score is not None and not domain.spam_score:
                domain.spam_score = metrics.spam_score
            if metrics.organic_traffic and not domain.organic_traffic:
                domain.organic_traffic = metrics.organic_traffic
            if metrics.domain_age_days and not domain.domain_age_days:
                domain.domain_age_days = metrics.domain_age_days

        # Use existing metrics if already populated (e.g. from external API sync),
        # otherwise use defaults that will fail vetting (forces manual data entry or API integration)
        dr = domain.dr or 0.0
        da = domain.da or 0.0
        spam_score = domain.spam_score or 0.0
        domain_age_days = domain.domain_age_days or 0
        organic_traffic = domain.organic_traffic or 0
        content_quality = domain.content_quality or 50.0
        is_pbn = domain.is_pbn or False

        # --- PRD vetting thresholds ---
        rejection_reasons: list[str] = []

        if dr < 5:
            rejection_reasons.append(f"DR {dr} is below minimum 5")
        if organic_traffic < 500:
            rejection_reasons.append(f"Organic traffic {organic_traffic} is below minimum 500/month")
        if spam_score >= 15.0:
            rejection_reasons.append(f"Spam score {spam_score}% exceeds maximum 15%")
        if domain_age_days < 180:
            rejection_reasons.append(f"Domain age {domain_age_days} days is below minimum 180 days (6 months)")
        if is_pbn:
            rejection_reasons.append("PBN pattern detected")

        # --- WTS formula (Weave Trust Score) ---
        traffic_legitimacy = min(organic_traffic / 1000, 100.0)
        link_profile = dr
        age_score = min(domain_age_days / 365 * 20, 100.0)

        wts = round(
            da * 0.30
            + content_quality * 0.25
            + traffic_legitimacy * 0.20
            + link_profile * 0.15
            + age_score * 0.10,
            2,
        )

        domain.wts = wts
        domain.vetted_at = datetime.now(timezone.utc)

        if rejection_reasons:
            domain.vetting_status = "rejected"
            domain.rejection_reason = "; ".join(rejection_reasons)
        elif wts < 30:
            domain.vetting_status = "rejected"
            domain.rejection_reason = f"WTS score {wts} is below the minimum threshold of 30"
        else:
            domain.vetting_status = "approved"
            domain.status = "active"
            domain.rejection_reason = None

        await db.commit()
        await db.refresh(domain)

        status_label = "approved" if domain.vetting_status == "approved" else "rejected"
        await NotificationService.create(
            db,
            domain.user_id,
            "domain_vetted",
            f"Domain vetting {status_label}",
            f"{domain.domain} has been {status_label}." + (f" Reason: {domain.rejection_reason}" if domain.rejection_reason else ""),
            {"domain_id": str(domain.id), "domain": domain.domain, "status": status_label},
        )

        return domain

    # --- List / Get / Delete ----------------------------------------------

    @staticmethod
    async def list_domains(
        db: AsyncSession, user_id: str
    ) -> list[Domain]:
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        result = await db.execute(
            select(Domain)
            .where(Domain.user_id == uid, Domain.status != "removed")
            .options(selectinload(Domain.credit_account))
            .order_by(Domain.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_domain(
        db: AsyncSession, domain_id: uuid.UUID
    ) -> Domain | None:
        result = await db.execute(
            select(Domain)
            .where(Domain.id == domain_id)
            .options(selectinload(Domain.credit_account))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_domain(
        db: AsyncSession, domain_id: uuid.UUID, user_id: str
    ) -> None:
        domain = await db.get(Domain, domain_id)
        if not domain:
            raise LookupError("Domain not found")
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        if domain.user_id != uid:
            raise PermissionError("Not your domain")
        domain.status = "removed"
        await db.commit()
