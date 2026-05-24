from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, regcomply, fxwatch, bursa_risk, survival_pro

app = FastAPI(
    title="MIFCG API",
    description="Malaysian Fintech Compliance Gateway — Backend API",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(regcomply.router)
app.include_router(fxwatch.router)
app.include_router(bursa_risk.router)
app.include_router(survival_pro.router)
