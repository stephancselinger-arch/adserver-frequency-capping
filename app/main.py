import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import caps, check

app = FastAPI(
    title="AdServer Frequency Capping",
    description=(
        "Redis-backed frequency capping microservice for programmatic advertising. "
        "Provides real-time impression counting with hourly / daily / weekly / lifetime "
        "windows across campaign, line item, creative, and advertiser dimensions. "
        "Falls back to in-memory store when Redis is not configured."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(caps.router, prefix="/v1")
app.include_router(check.router, prefix="/v1")


@app.get("/health")
def health():
    redis_url = os.getenv("REDIS_URL", "")
    return {
        "status": "ok",
        "service": "adserver-frequency-capping",
        "backend": "redis" if redis_url else "memory",
    }
