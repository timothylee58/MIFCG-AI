from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.core.limiter import limiter

router = APIRouter(
    prefix="/api/fxwatch",
    tags=["fxwatch"],
    dependencies=[Depends(get_current_user)],
)

MYR_PAIRS = ["USD/MYR", "EUR/MYR", "GBP/MYR", "JPY/MYR", "SGD/MYR", "CNY/MYR"]


class FXAlert(BaseModel):
    pair: str
    threshold: float
    direction: str  # "above" | "below"


@router.get("/")
async def fxwatch_info():
    return {
        "module": "FXWatch",
        "status": "scaffold",
        "pairs": MYR_PAIRS,
        "endpoints": ["/rates", "/stream", "/alerts"],
    }


@router.get("/rates")
@limiter.limit("20/minute")
async def get_rates(request: Request):
    """Phase 0+: Will return cached BNM FX rates from Redis."""
    raise HTTPException(
        status_code=501,
        detail="FX rate fetching not yet implemented.",
    )


@router.get("/stream")
@limiter.limit("20/minute")
async def stream_rates(request: Request):
    """Phase 0+: Will SSE-stream live FX tick data."""
    raise HTTPException(status_code=501, detail="SSE stream not yet implemented.")


@router.post("/alerts")
@limiter.limit("20/minute")
async def create_alert(request: Request, alert: FXAlert):
    raise HTTPException(status_code=501, detail="Alerts not yet implemented.")
