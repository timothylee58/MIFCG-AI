from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/bursa-risk", tags=["bursa-risk"])

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
async def get_factor_scores(body: FactorScoreRequest):
    """Phase 3: XGBoost factor score inference."""
    raise HTTPException(
        status_code=501,
        detail="Bursa factor model not yet trained. Coming in Phase 3.",
    )


@router.get("/screener")
async def run_screener(
    min_score: float = 60.0,
    shariah_only: bool = False,
):
    raise HTTPException(status_code=501, detail="Phase 3.")
