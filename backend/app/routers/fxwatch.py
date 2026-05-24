from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/fxwatch", tags=["fxwatch"])

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
async def get_rates():
    """Phase 0+: Will return cached BNM FX rates from Redis."""
    raise HTTPException(
        status_code=501,
        detail="FX rate fetching not yet implemented.",
    )


@router.get("/stream")
async def stream_rates():
    """Phase 0+: Will SSE-stream live FX tick data."""
    raise HTTPException(status_code=501, detail="SSE stream not yet implemented.")


@router.post("/alerts")
async def create_alert(alert: FXAlert):
    raise HTTPException(status_code=501, detail="Alerts not yet implemented.")
