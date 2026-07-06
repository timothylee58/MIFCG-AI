from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.core.limiter import limiter

router = APIRouter(
    prefix="/api/bursa-risk",
    tags=["bursa-risk"],
    dependencies=[Depends(get_current_user)],
)

KLCI_COMPONENTS = [
    "MAYBANK", "CIMB", "PBB", "TENAGA", "PCHEM", "RHBBANK",
    "AXIATA", "MAXIS", "DIGI", "HLBANK", "AMBANK", "IOICORP",
    "SIMEPLT", "GENM", "AIRASIA", "PETDAG", "MISC", "HAPSENG",
    "KLK", "PPB",
]


class FactorScoreRequest(BaseModel):
    tickers: list[str] = KLCI_COMPONENTS[:10]
    factors: list[str] = ["value", "momentum", "quality", "low_vol", "dividend"]


@router.get("/")
async def bursa_risk_info():
    return {
        "module": "Bursa Risk",
        "status": "scaffold",
        "universe": f"KLCI ({len(KLCI_COMPONENTS)} components)",
        "endpoints": ["/scores", "/backtest", "/screener"],
    }


@router.post("/scores")
@limiter.limit("20/minute")
async def get_factor_scores(request: Request, body: FactorScoreRequest):
    """Phase 3: XGBoost factor score inference."""
    raise HTTPException(
        status_code=501,
        detail="Bursa factor model not yet trained. Coming in Phase 3.",
    )


@router.get("/screener")
@limiter.limit("20/minute")
async def run_screener(
    request: Request,
    min_score: float = 60.0,
    shariah_only: bool = False,
):
    raise HTTPException(status_code=501, detail="Phase 3.")
