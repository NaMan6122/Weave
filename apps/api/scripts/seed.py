"""
Seed script — populates the database with realistic synthetic data for development.

Creates:
- 1 test user
- 50 domains across 10 niches (verified, vetted, active)
- 3-5 articles per domain (~200 total) with embeddings
- Credit accounts with starting balance
- ~50 link placements between domains

Run: cd apps/api && .venv/bin/python scripts/seed.py
Requires: DATABASE_URL set in .env or environment
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent to path for app imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dependencies import async_session, engine
from app.models.base import Base
from app.models.user import User
from app.models.domain import Domain
from app.models.page import Page
from app.models.credit import CreditAccount, CreditTransaction
from app.models.link import Link
from app.services.embeddings import EmbeddingService
from app.services.credits import credit_value

NICHES = [
    "fitness", "finance", "technology", "health", "marketing",
    "travel", "food", "education", "real-estate", "saas",
]

DOMAIN_TEMPLATES = [
    # (domain_pattern, dr_range, traffic_range, age_days_range)
    ("{niche}guide.com", (15, 45), (2000, 30000), (200, 1200)),
    ("the{niche}blog.com", (10, 35), (1000, 15000), (180, 900)),
    ("{niche}insider.io", (20, 55), (5000, 80000), (300, 2000)),
    ("{niche}hub.co", (8, 30), (800, 12000), (180, 600)),
    ("pro{niche}.com", (25, 60), (10000, 100000), (400, 2500)),
]

ARTICLE_TEMPLATES = {
    "fitness": [
        "Complete Guide to Building Muscle at Home",
        "10 Best Protein Sources for Athletes",
        "HIIT vs Steady State Cardio: What Science Says",
        "Recovery Techniques for Serious Lifters",
        "Beginner's Guide to Strength Training",
    ],
    "finance": [
        "How to Start Investing with $500",
        "Understanding Index Funds vs ETFs",
        "Building an Emergency Fund: Step by Step",
        "Tax-Efficient Investing Strategies",
        "Budgeting Methods That Actually Work",
    ],
    "technology": [
        "Introduction to Large Language Models",
        "Building REST APIs with Python FastAPI",
        "Docker Containerization Best Practices",
        "Understanding WebSockets for Real-Time Apps",
        "CI/CD Pipeline Setup Guide",
    ],
    "health": [
        "Sleep Optimization: Science-Backed Tips",
        "Understanding Gut Health and Probiotics",
        "Mental Health Benefits of Daily Exercise",
        "Anti-Inflammatory Diet Guide",
        "Stress Management Techniques That Work",
    ],
    "marketing": [
        "SEO Fundamentals for 2025",
        "Content Marketing Strategy Framework",
        "Email Marketing Automation Guide",
        "Social Media Algorithm Changes Explained",
        "Conversion Rate Optimization Basics",
    ],
    "travel": [
        "Budget Travel Tips for Southeast Asia",
        "Remote Work and Travel: Digital Nomad Guide",
        "Best Travel Credit Cards Compared",
        "Solo Travel Safety Tips",
        "How to Plan a Multi-City Trip",
    ],
    "food": [
        "Meal Prep Guide for Busy Professionals",
        "Plant-Based Cooking for Beginners",
        "Understanding Fermentation at Home",
        "Kitchen Equipment Worth Investing In",
        "Quick Healthy Recipes Under 30 Minutes",
    ],
    "education": [
        "Online Learning Platforms Compared",
        "How to Build a Self-Study Curriculum",
        "Speed Reading Techniques That Work",
        "Note-Taking Methods for Better Retention",
        "Career Switching Through Online Education",
    ],
    "real-estate": [
        "First-Time Home Buyer Checklist",
        "Real Estate Investment for Beginners",
        "Understanding Property Valuations",
        "Rental Property Management Tips",
        "Commercial vs Residential Investing",
    ],
    "saas": [
        "SaaS Pricing Strategy Guide",
        "Building a Product-Led Growth Engine",
        "Customer Onboarding Best Practices",
        "Reducing Churn: Retention Strategies",
        "SaaS Metrics Every Founder Should Track",
    ],
}


def _generate_article_content(title: str, niche: str) -> str:
    """Generate realistic-looking article content for embedding."""
    intro = f"This comprehensive guide covers everything you need to know about {title.lower()}. "
    body = f"In the {niche} space, understanding these concepts is crucial for success. "
    details = f"We'll explore practical strategies, backed by research and real-world examples. "
    conclusion = f"Whether you're a beginner or experienced, this {niche} resource will help you level up."
    # Pad to ~500 words for a meaningful embedding
    filler_topics = [
        f"Key principles of {niche} that every professional should understand.",
        f"Common mistakes people make when getting started with {title.lower()}.",
        f"Expert tips from leading {niche} practitioners.",
        f"Step-by-step approach to implementing these {niche} strategies.",
        f"How to measure success and track progress in your {niche} journey.",
    ]
    return " ".join([intro, body, details, conclusion] + filler_topics * 3)


SEED_USERS = [
    {"email": "admin@weave.io", "name": "Weave Admin", "plan": "admin"},
    {"email": "alice@example.com", "name": "Alice Chen", "plan": "pro"},
    {"email": "bob@example.com", "name": "Bob Martinez", "plan": "pro"},
    {"email": "carol@example.com", "name": "Carol Nguyen", "plan": "starter"},
    {"email": "dave@example.com", "name": "Dave Wilson", "plan": "starter"},
    {"email": "eve@example.com", "name": "Eve Johnson", "plan": "pro"},
]


async def seed(db: AsyncSession) -> None:
    print("Seeding database...")

    # 1. Create users
    users: list[User] = []
    for u in SEED_USERS:
        user = User(id=uuid.uuid4(), **u)
        db.add(user)
        users.append(user)
    await db.flush()
    print(f"  Created {len(users)} users")

    # 2. Create domains
    domains: list[Domain] = []
    now = datetime.now(timezone.utc)

    for i, niche in enumerate(NICHES):
        # 5 domains per niche = 50 total
        for j, template in enumerate(DOMAIN_TEMPLATES):
            pattern, dr_range, traffic_range, age_range = template
            domain_name = pattern.format(niche=niche)

            dr = random.randint(*dr_range)
            traffic = random.randint(*traffic_range)
            age_days = random.randint(*age_range)
            spam = round(random.uniform(0.5, 8.0), 1)

            owner = users[(i * len(DOMAIN_TEMPLATES) + j) % len(users)]

            domain = Domain(
                id=uuid.uuid4(),
                user_id=owner.id,
                domain=domain_name,
                dr=dr,
                da=dr + random.randint(-5, 10),
                organic_traffic=traffic,
                domain_age_days=age_days,
                spam_score=spam,
                content_quality=random.uniform(50, 90),
                niche=niche,
                language="en",
                status="active",
                verified=True,
                verification_token=uuid.uuid4().hex,
                vetting_status="approved",
                wts=random.uniform(40, 85),
                vetted_at=now - timedelta(days=random.randint(1, 30)),
            )
            db.add(domain)
            domains.append(domain)

    await db.flush()
    print(f"  Created {len(domains)} domains across {len(NICHES)} niches")

    # 3. Create credit accounts
    for domain in domains:
        starting_balance = Decimal(str(random.randint(200, 2000)))
        account = CreditAccount(
            domain_id=domain.id,
            balance=starting_balance,
            lifetime_earned=starting_balance + Decimal(str(random.randint(0, 500))),
            lifetime_spent=Decimal(str(random.randint(0, 300))),
        )
        db.add(account)
    await db.flush()
    print("  Created credit accounts")

    # 4. Create articles with embeddings
    pages: list[Page] = []
    for domain in domains:
        niche = domain.niche or "technology"
        articles = ARTICLE_TEMPLATES.get(niche, ARTICLE_TEMPLATES["technology"])
        num_articles = random.randint(3, 5)

        for title in articles[:num_articles]:
            content = _generate_article_content(title, niche)
            slug = title.lower().replace(" ", "-").replace(":", "").replace("'", "")
            url = f"https://{domain.domain}/{slug}"

            # Use sync hash embedding (no API key needed for seeding)
            embedding = EmbeddingService.embed_text_sync(content)

            page = Page(
                id=uuid.uuid4(),
                domain_id=domain.id,
                url=url,
                title=title,
                niche=niche,
                language="en",
                word_count=len(content.split()),
                embedding=embedding,
                status="active",
                created_at=now - timedelta(days=random.randint(1, 365)),
            )
            db.add(page)
            pages.append(page)

    await db.flush()
    print(f"  Created {len(pages)} articles with embeddings")

    # 5. Create some link placements
    link_count = 0
    placed_pairs: set[tuple] = set()

    for _ in range(60):
        source_page = random.choice(pages)
        # Pick a target from a different domain in same or related niche
        source_domain = next(d for d in domains if d.id == source_page.domain_id)
        same_niche_pages = [
            p for p in pages
            if p.domain_id != source_page.domain_id
            and any(d.id == p.domain_id and d.niche == source_domain.niche for d in domains)
        ]
        if not same_niche_pages:
            continue

        target_page = random.choice(same_niche_pages)
        pair = (source_page.id, target_page.id)
        if pair in placed_pairs:
            continue
        placed_pairs.add(pair)

        target_domain = next(d for d in domains if d.id == target_page.domain_id)
        anchor = " ".join((target_page.title or "link").split()[:4])

        link = Link(
            source_page_id=source_page.id,
            target_page_id=target_page.id,
            source_domain_id=source_page.domain_id,
            target_domain_id=target_page.domain_id,
            anchor_text=anchor,
            match_score=Decimal(str(round(random.uniform(0.5, 0.95), 4))),
            match_breakdown={
                "semantic_similarity": round(random.uniform(0.6, 0.98), 4),
                "dr_proximity": round(random.uniform(0.5, 1.0), 4),
                "traffic_freshness": round(random.uniform(0.3, 0.9), 4),
            },
            placement_type="body",
            credits_earned=Decimal(str(credit_value(source_domain.dr or 10))),
            status=random.choice(["live", "live", "live", "placed"]),
            placed_at=now - timedelta(days=random.randint(1, 60)),
            verified_at=now - timedelta(days=random.randint(0, 7)),
            sla_expires_at=now + timedelta(days=random.randint(30, 90)),
        )
        db.add(link)
        link_count += 1

    await db.flush()
    await db.commit()
    print(f"  Created {link_count} link placements")
    print(f"\nSeed complete! Total: {len(domains)} domains, {len(pages)} articles, {link_count} links")
    print(f"Users: {', '.join(u.email for u in users)}")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(Domain))
        count = result.scalar_one()
        if count > 0:
            print(f"Database already has {count} domains. Skipping seed.")
            print("To re-seed, drop and recreate the database first.")
            return

        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
