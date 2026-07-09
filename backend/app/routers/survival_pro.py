import json
import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from app.core.auth import get_current_user
from app.core.limiter import limiter
from app.services.survival_pro import (
    check_eligibility as run_eligibility,
    EligibilityProfile,
)
from app.services.survival_pro.schemes import ALL_SCHEMES
from app.services.survival_pro.spend_coach import stream_spend_coach

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/survival-pro",
    tags=["survival-pro"],
    dependencies=[Depends(get_current_user)],
)


# ─── Request / Response models ──────────────────────────────────────────────

class EligibilityRequest(BaseModel):
    monthly_income_myr: float = Field(..., gt=0)
    household_size: int = Field(..., ge=1)
    state: str
    age: int = Field(35, ge=18, le=100)
    has_epf: bool = True
    is_disabled: bool = False
    is_single_mother: bool = False
    has_ptptn_loan: bool = False
    has_children_under_18: bool = False
    employment_status: str = "employed"


class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str


class SpendCoachRequest(BaseModel):
    messages: list[ChatMessage]
    monthly_income: float = Field(..., gt=0)
    household_size: int = Field(1, ge=1)


# ─── Routes ─────────────────────────────────────────────────────────────────

@router.get("/")
async def survival_pro_info():
    return {
        "module": "Survival Pro",
        "status": "active",
        "schemes_available": len(ALL_SCHEMES),
        "endpoints": ["/eligibility", "/schemes", "/spend-coach"],
    }


@router.get("/schemes")
async def list_schemes():
    return {
        "schemes": [
            {
                "id": s.id,
                "name": s.name,
                "short_name": s.short_name,
                "category": s.category,
                "description": s.description,
                "how_to_apply": s.how_to_apply,
                "amount_label": s.amount_label,
                "tags": s.tags,
            }
            for s in ALL_SCHEMES
        ]
    }


@router.post("/eligibility")
async def check_eligibility(body: EligibilityRequest):
    profile = EligibilityProfile(
        monthly_income_myr=body.monthly_income_myr,
        household_size=body.household_size,
        state=body.state,
        age=body.age,
        has_epf=body.has_epf,
        is_disabled=body.is_disabled,
        is_single_mother=body.is_single_mother,
        has_ptptn_loan=body.has_ptptn_loan,
        has_children_under_18=body.has_children_under_18,
        employment_status=body.employment_status,
    )
    results = run_eligibility(profile)
    return {
        "results": [
            {
                "scheme_id": r.scheme.id,
                "scheme_name": r.scheme.name,
                "scheme_short_name": r.scheme.short_name,
                "category": r.scheme.category,
                "eligible": r.eligible,
                "reason": r.reason,
                "estimated_amount": r.estimated_amount,
                "how_to_apply": r.scheme.how_to_apply,
                "tags": r.scheme.tags,
            }
            for r in results
        ],
        "eligible_count": sum(1 for r in results if r.eligible),
        "total_count": len(results),
    }


@router.post("/spend-coach")
@limiter.limit("20/minute")
async def spend_coach_chat(request: Request, body: SpendCoachRequest):
    async def event_stream():
        try:
            messages = [{"role": m.role, "content": m.content} for m in body.messages]
            async for chunk in stream_spend_coach(
                messages=messages,
                monthly_income=body.monthly_income,
                household_size=body.household_size,
            ):
                yield {"data": json.dumps({"type": "chunk", "text": chunk})}
            yield {"data": json.dumps({"type": "done"})}
        except Exception as exc:
            logger.exception("Spend coach error")
            yield {"data": json.dumps({"type": "error", "message": str(exc)})}

    return EventSourceResponse(event_stream())
