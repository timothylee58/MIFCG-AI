import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.survival_pro.eligibility import (
    EligibilityProfile,
    check_eligibility,
    eligible_only,
)


# ─── Unit tests: eligibility engine ─────────────────────────────────────────

def make_profile(**kwargs) -> EligibilityProfile:
    defaults = dict(
        monthly_income_myr=2500,
        household_size=3,
        state="Selangor",
        age=35,
        has_epf=True,
        is_disabled=False,
        is_single_mother=False,
        has_ptptn_loan=False,
        has_children_under_18=True,
        employment_status="employed",
    )
    defaults.update(kwargs)
    return EligibilityProfile(**defaults)


def test_str_eligible_low_income_family():
    p = make_profile(monthly_income_myr=2500, household_size=3)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["str"].eligible
    assert "RM2,000" in results["str"].estimated_amount


def test_str_single_high_income_ineligible():
    p = make_profile(monthly_income_myr=6000, household_size=1, has_children_under_18=False)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["str"].eligible


def test_str_mid_bracket_single_ineligible():
    p = make_profile(monthly_income_myr=4000, household_size=1, has_children_under_18=False)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["str"].eligible


def test_str_mid_bracket_family_eligible():
    p = make_profile(monthly_income_myr=4000, household_size=2)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["str"].eligible
    assert "RM1,500" in results["str"].estimated_amount


def test_socso_employed():
    p = make_profile(employment_status="employed")
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["socso_eis"].eligible


def test_socso_unemployed():
    p = make_profile(employment_status="unemployed")
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["socso_eis"].eligible


def test_epf_no_contributor():
    p = make_profile(has_epf=False)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["epf_akaun3"].eligible


def test_mysalam_b40_eligible():
    p = make_profile(monthly_income_myr=3000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["mysalam"].eligible


def test_mysalam_above_threshold():
    p = make_profile(monthly_income_myr=5000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["mysalam"].eligible


def test_peka_age_and_income():
    p = make_profile(age=55, monthly_income_myr=3000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["peka_b40"].eligible


def test_peka_too_young():
    p = make_profile(age=40, monthly_income_myr=3000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["peka_b40"].eligible


def test_jkm_disabled_low_income():
    p = make_profile(is_disabled=True, monthly_income_myr=1500)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["jkm_aid"].eligible


def test_jkm_not_vulnerable():
    p = make_profile(is_disabled=False, is_single_mother=False, age=35, monthly_income_myr=1500)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["jkm_aid"].eligible


def test_ptptn_moratorium_very_low_income():
    p = make_profile(has_ptptn_loan=True, monthly_income_myr=1800)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert results["ptptn"].eligible
    assert "moratorium" in results["ptptn"].reason.lower()


def test_ptptn_no_loan():
    p = make_profile(has_ptptn_loan=False)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert not results["ptptn"].eligible


def test_selangor_aid_included():
    p = make_profile(state="Selangor", monthly_income_myr=3000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert "selangor_aid" in results
    assert results["selangor_aid"].eligible


def test_kl_aid_kuala_lumpur():
    p = make_profile(state="Kuala Lumpur", monthly_income_myr=3000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert "kl_aid" in results
    assert results["kl_aid"].eligible


def test_no_state_aid_for_other_state():
    p = make_profile(state="Johor", monthly_income_myr=2000)
    results = {r.scheme.id: r for r in check_eligibility(p)}
    assert "selangor_aid" not in results
    assert "kl_aid" not in results


def test_eligible_only_filter():
    p = make_profile(monthly_income_myr=2000, has_epf=True, employment_status="employed")
    all_results = check_eligibility(p)
    eligible = eligible_only(all_results)
    assert all(r.eligible for r in eligible)
    assert len(eligible) < len(all_results)


# ─── API integration tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_survival_pro_info():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/survival-pro/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["schemes_available"] > 0


@pytest.mark.asyncio
async def test_list_schemes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/survival-pro/schemes")
    assert r.status_code == 200
    schemes = r.json()["schemes"]
    assert len(schemes) >= 9
    ids = [s["id"] for s in schemes]
    assert "str" in ids
    assert "mysalam" in ids


@pytest.mark.asyncio
async def test_eligibility_endpoint_b40():
    payload = {
        "monthly_income_myr": 2000,
        "household_size": 4,
        "state": "Selangor",
        "age": 38,
        "has_epf": True,
        "is_disabled": False,
        "is_single_mother": False,
        "has_ptptn_loan": False,
        "has_children_under_18": True,
        "employment_status": "employed",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/survival-pro/eligibility", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["eligible_count"] > 0
    assert data["total_count"] >= data["eligible_count"]
    scheme_ids = [item["scheme_id"] for item in data["results"]]
    assert "str" in scheme_ids


@pytest.mark.asyncio
async def test_eligibility_endpoint_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/survival-pro/eligibility", json={"monthly_income_myr": -100, "household_size": 1, "state": "KL"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_spend_coach_streams():
    payload = {
        "messages": [{"role": "user", "content": "I earn RM2,500/month. How should I budget?"}],
        "monthly_income": 2500.0,
        "household_size": 2,
    }

    async def fake_stream(*args, **kwargs):
        for token in ["Here", " is", " your", " budget."]:
            yield token

    with patch("app.routers.survival_pro.stream_spend_coach", side_effect=fake_stream):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/api/survival-pro/spend-coach", json=payload)
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
