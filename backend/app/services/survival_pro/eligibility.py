"""
Rule-based eligibility matcher for Malaysian welfare schemes.
Returns matched schemes with the reason and estimated benefit amount.
"""

from dataclasses import dataclass
from .schemes import (
    Scheme, ALL_SCHEMES,
    STR, SOCSO_EIS, EPF_AKAUN3, MYSALAM, PEKA_B40,
    JKM_AID, PTPTN_MORATORIUM, SELANGOR_AID, KL_AID,
)


@dataclass
class EligibilityResult:
    scheme: Scheme
    eligible: bool
    reason: str
    estimated_amount: str   # human-readable


@dataclass
class EligibilityProfile:
    monthly_income_myr: float
    household_size: int
    state: str              # e.g. "Selangor", "Kuala Lumpur", "Johor"
    age: int = 35
    has_epf: bool = True
    is_disabled: bool = False
    is_single_mother: bool = False
    has_ptptn_loan: bool = False
    has_children_under_18: bool = False
    employment_status: str = "employed"  # "employed" | "self-employed" | "unemployed"


def _str_eligibility(p: EligibilityProfile) -> EligibilityResult:
    annual = p.monthly_income_myr * 12
    # Household income threshold
    if p.monthly_income_myr <= 3000:
        if p.household_size >= 2 or p.has_children_under_18:
            return EligibilityResult(STR, True, "Household income ≤ RM3,000/month", "RM2,000/year")
        else:
            return EligibilityResult(STR, True, "Single/no dependants, income ≤ RM3,000/month", "RM500/year")
    elif p.monthly_income_myr <= 5000:
        if p.household_size >= 2 or p.has_children_under_18:
            return EligibilityResult(STR, True, "Household income RM3,001–RM5,000/month", "RM1,500/year")
        else:
            return EligibilityResult(STR, False, "Single applicants in RM3K–RM5K bracket not eligible for STR household tier", "—")
    else:
        return EligibilityResult(STR, False, "Household income exceeds RM5,000/month STR threshold", "—")


def _socso_eligibility(p: EligibilityProfile) -> EligibilityResult:
    if p.employment_status == "employed":
        return EligibilityResult(
            SOCSO_EIS, True,
            "Private-sector employees are mandatorily covered",
            "EIS benefit up to 60% of insured salary for 3–6 months",
        )
    elif p.employment_status == "self-employed":
        return EligibilityResult(
            SOCSO_EIS, True,
            "Self-employed can voluntarily contribute to SOCSO",
            "Voluntary scheme — contribution from RM14.05/month",
        )
    return EligibilityResult(SOCSO_EIS, False, "Not currently in paid employment", "—")


def _epf_eligibility(p: EligibilityProfile) -> EligibilityResult:
    if p.has_epf:
        return EligibilityResult(
            EPF_AKAUN3, True,
            "Active EPF contributor — 10% of balance in flexible Akaun 3",
            "10% of your total EPF balance, withdrawable anytime",
        )
    return EligibilityResult(EPF_AKAUN3, False, "Not an EPF contributor (self-employed may opt in voluntarily)", "—")


def _mysalam_eligibility(p: EligibilityProfile) -> EligibilityResult:
    if p.monthly_income_myr <= 4849:
        return EligibilityResult(
            MYSALAM, True,
            "B40 income bracket — auto-enrolled if registered in eKasih",
            "RM8,000 hospitalisation income replacement + critical illness cover",
        )
    return EligibilityResult(MYSALAM, False, "Income above B40 threshold for MySalam", "—")


def _peka_eligibility(p: EligibilityProfile) -> EligibilityResult:
    if p.age >= 50 and p.monthly_income_myr <= 4849:
        return EligibilityResult(PEKA_B40, True, "Age ≥ 50 and B40 income bracket", "Free health screening at any Klinik Kesihatan")
    reason = "Age < 50" if p.age < 50 else "Income above B40 threshold"
    return EligibilityResult(PEKA_B40, False, reason, "—")


def _jkm_eligibility(p: EligibilityProfile) -> EligibilityResult:
    qualifying = p.is_disabled or p.is_single_mother or (p.age >= 60 and p.monthly_income_myr < 1000)
    if qualifying and p.monthly_income_myr < 2000:
        category = (
            "OKU (disabled)" if p.is_disabled
            else "single mother" if p.is_single_mother
            else "elderly (60+) with very low income"
        )
        return EligibilityResult(JKM_AID, True, f"Qualifies as {category}", "RM300–RM500/month")
    return EligibilityResult(JKM_AID, False, "Does not meet JKM vulnerable-group criteria", "—")


def _ptptn_eligibility(p: EligibilityProfile) -> EligibilityResult:
    if p.has_ptptn_loan:
        if p.monthly_income_myr < 2000:
            return EligibilityResult(PTPTN_MORATORIUM, True, "Income below RM2,000 — qualifies for full moratorium", "Repayment deferred; no interest accrual during deferment")
        return EligibilityResult(PTPTN_MORATORIUM, True, "Active PTPTN borrower — 15% settlement discount available", "15% discount on full outstanding balance")
    return EligibilityResult(PTPTN_MORATORIUM, False, "No PTPTN loan", "—")


def _state_eligibility(p: EligibilityProfile) -> list[EligibilityResult]:
    results = []
    state_lower = p.state.lower()
    if "selangor" in state_lower and p.monthly_income_myr <= 4000:
        results.append(EligibilityResult(SELANGOR_AID, True, "Selangor resident with household income ≤ RM4,000", "Free 20m³ water + up to RM300/month"))
    if ("kuala lumpur" in state_lower or "kl" in state_lower or "federal territory" in state_lower or "putrajaya" in state_lower) and p.monthly_income_myr <= 3500:
        results.append(EligibilityResult(KL_AID, True, "Federal Territory resident with income ≤ RM3,500/month", "RM300–RM600/month + supplements"))
    return results


def check_eligibility(profile: EligibilityProfile) -> list[EligibilityResult]:
    """
    Run all eligibility rules and return results for every scheme,
    eligible and ineligible, so the frontend can show both.
    """
    results = [
        _str_eligibility(profile),
        _socso_eligibility(profile),
        _epf_eligibility(profile),
        _mysalam_eligibility(profile),
        _peka_eligibility(profile),
        _jkm_eligibility(profile),
        _ptptn_eligibility(profile),
    ]
    results.extend(_state_eligibility(profile))
    return results


def eligible_only(results: list[EligibilityResult]) -> list[EligibilityResult]:
    return [r for r in results if r.eligible]
