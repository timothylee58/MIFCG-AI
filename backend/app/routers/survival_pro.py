from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/survival-pro", tags=["survival-pro"])


class EligibilityRequest(BaseModel):
    monthly_income_myr: float
    household_size: int
    state: str
    has_epf: bool = True
    is_disabled: bool = False
    has_children_under_18: bool = False


@router.get("/")
async def survival_pro_info():
    return {
        "module": "Survival Pro",
        "status": "scaffold",
        "schemes": ["SOCSO", "EPF", "BSH", "BRIM", "STR", "state_aid"],
        "endpoints": ["/eligibility", "/schemes", "/spend-coach"],
    }


@router.post("/eligibility")
async def check_eligibility(body: EligibilityRequest):
    """Phase 2: Matches household to eligible aid schemes."""
    raise HTTPException(
        status_code=501,
        detail="Eligibility matcher not yet implemented. Coming in Phase 2.",
    )


@router.get("/schemes")
async def list_schemes(state: str | None = None):
    raise HTTPException(status_code=501, detail="Phase 2.")


@router.post("/spend-coach")
async def spend_coach_chat():
    raise HTTPException(status_code=501, detail="Phase 2.")
