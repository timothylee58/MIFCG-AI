from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import health, regcomply, fxwatch, bursa_risk, survival_pro
from app.services.fxwatch.scheduler import start_fxwatch_scheduler, stop_fxwatch_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip the live polling scheduler during tests — it would otherwise fire
    # real HTTP calls to BNM/Anthropic/Slack/Telegram on a background timer
    # while the test suite runs.
    if settings.environment != "test":
        start_fxwatch_scheduler()
    yield
    if settings.environment != "test":
        stop_fxwatch_scheduler()


app = FastAPI(
    title="MIFCG API",
    description="Malaysian Fintech Compliance Gateway — Backend API",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router)
app.include_router(regcomply.router)
app.include_router(fxwatch.router)
app.include_router(bursa_risk.router)
app.include_router(survival_pro.router)
