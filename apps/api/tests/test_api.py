import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestDomainsEndpoints:
    async def test_list_domains_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/domains/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domains"] == []
        assert data["total"] == 0

    async def test_create_domain(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/domains/",
            json={"domain": "example.com", "niche": "tech", "language": "en"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["domain"] == "example.com"
        assert data["status"] == "pending"
        assert data["verified"] is False

    async def test_create_domain_then_list(self, client: AsyncClient):
        await client.post(
            "/api/v1/domains/",
            json={"domain": "listed.com"},
        )
        resp = await client.get("/api/v1/domains/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        domains = [d["domain"] for d in data["domains"]]
        assert "listed.com" in domains

    async def test_create_duplicate_domain_returns_409(self, client: AsyncClient):
        await client.post("/api/v1/domains/", json={"domain": "dup.com"})
        resp = await client.post("/api/v1/domains/", json={"domain": "dup.com"})
        assert resp.status_code == 409
