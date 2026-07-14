from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, billing, credits, domains, links, matching, network, webhooks

app = FastAPI(title="Weave API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(domains.router, prefix="/api/v1/domains", tags=["domains"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["matching"])
app.include_router(credits.router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(links.router, prefix="/api/v1/links", tags=["links"])
app.include_router(network.router, prefix="/api/v1/network", tags=["network"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
