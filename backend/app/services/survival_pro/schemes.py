"""
Malaysian welfare scheme definitions.
All amounts in MYR/year unless stated.
"""

from dataclasses import dataclass, field


@dataclass
class Scheme:
    id: str
    name: str
    short_name: str
    category: str           # "Cash Aid" | "Employment" | "Health" | "Education" | "State"
    description: str
    how_to_apply: str
    amount_label: str       # human-readable amount/benefit description
    source_url: str = ""
    tags: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────
# Scheme definitions
# ─────────────────────────────────────────────────────────

STR = Scheme(
    id="str",
    name="Sumbangan Tunai Rahmah (STR)",
    short_name="STR",
    category="Cash Aid",
    description=(
        "Direct annual cash transfer for B40 households. Replaces BSH. "
        "Disbursed in quarterly instalments."
    ),
    how_to_apply="Register at https://str.hasil.gov.my or Pos Malaysia / LHDN branches.",
    amount_label="RM2,000/yr (income < RM3K) · RM1,500/yr (RM3K–RM5K) · RM500 singles",
    tags=["B40", "cash", "federal"],
)

SOCSO_EIS = Scheme(
    id="socso_eis",
    name="SOCSO / EIS Employment Benefits",
    short_name="SOCSO",
    category="Employment",
    description=(
        "PERKESO provides employment injury protection, invalidity scheme, "
        "and Employment Insurance System (EIS) retrenchment benefits. "
        "Mandatory for all private-sector employees."
    ),
    how_to_apply="Auto-enrolled by employer. Check benefits at mysocso.com.my.",
    amount_label="EIS: up to RM6,000/month for 6 months post-retrenchment",
    tags=["employment", "insurance", "mandatory"],
)

EPF_AKAUN3 = Scheme(
    id="epf_akaun3",
    name="EPF Akaun 3 (Flexible Account)",
    short_name="EPF Akaun 3",
    category="Employment",
    description=(
        "EPF's third account introduced in 2024 allows members to withdraw "
        "savings for immediate needs without early withdrawal penalties on the full amount."
    ),
    how_to_apply="Apply via i-Akaun (EPF portal) or any EPF branch.",
    amount_label="10% of EPF balance moved to Akaun 3; withdrawable anytime",
    tags=["EPF", "savings", "flexible"],
)

MYSALAM = Scheme(
    id="mysalam",
    name="MySalam — National Health Protection Scheme",
    short_name="MySalam",
    category="Health",
    description=(
        "Free health insurance for B40 Malaysians. Covers 45 critical illnesses "
        "and hospitalisation income replacement up to RM8,000/year."
    ),
    how_to_apply="Auto-enrolled if listed in eKasih / JKM database. Verify at mysalam.com.my.",
    amount_label="RM8,000 hospitalisation / RM1,000–RM8,000 for critical illness",
    tags=["health", "insurance", "B40", "free"],
)

PEKA_B40 = Scheme(
    id="peka_b40",
    name="Peka B40 Health Screening",
    short_name="Peka B40",
    category="Health",
    description=(
        "Free health screening for Malaysians aged 50+ in the B40 group. "
        "Covers non-communicable diseases and mental health assessments."
    ),
    how_to_apply="Attend any Klinik Kesihatan or registered private clinic with MyKad.",
    amount_label="Free screening for 15+ health indicators",
    tags=["health", "screening", "50+", "B40"],
)

JKM_AID = Scheme(
    id="jkm_aid",
    name="JKM Welfare Aid (Bantuan Kebajikan)",
    short_name="JKM Aid",
    category="Cash Aid",
    description=(
        "Department of Social Welfare monthly cash assistance for vulnerable groups: "
        "single mothers, elderly, persons with disabilities (OKU), and hardcore poor."
    ),
    how_to_apply="Apply at nearest Jabatan Kebajikan Masyarakat (JKM) district office.",
    amount_label="RM300–RM500/month depending on category",
    tags=["welfare", "disabled", "elderly", "single-mother"],
)

BRIM_HISTORICAL = Scheme(
    id="brim",
    name="BR1M / BSH (Historical — replaced by STR)",
    short_name="BR1M/BSH",
    category="Cash Aid",
    description=(
        "Bantuan Rakyat 1Malaysia (BR1M) and Bantuan Sara Hidup (BSH) were the predecessors "
        "to STR. Recipients auto-migrated. Check if you're still eligible under STR."
    ),
    how_to_apply="Legacy recipients automatically enrolled in STR. Verify at str.hasil.gov.my.",
    amount_label="Replaced by STR — check STR eligibility",
    tags=["historical", "B40"],
)

PTPTN_MORATORIUM = Scheme(
    id="ptptn",
    name="PTPTN Repayment Assistance",
    short_name="PTPTN Aid",
    category="Education",
    description=(
        "PTPTN offers repayment moratoriums and restructuring for borrowers "
        "earning below RM2,000/month. Full settlement discounts also available."
    ),
    how_to_apply="Apply online at ptptn.gov.my or visit any PTPTN branch.",
    amount_label="Moratorium (< RM2K income) · 15% discount for full settlement",
    tags=["education", "loan", "moratorium"],
)

SELANGOR_AID = Scheme(
    id="selangor_aid",
    name="Selangor Smart Saver / Selangor Care",
    short_name="Selangor Aid",
    category="State",
    description=(
        "State-level welfare programmes including Selangor Care monthly aid, "
        "free water quota (20 cubic metres), and school aid for Selangor residents."
    ),
    how_to_apply="Apply at Pusat Perkhidmatan Setempat (PPS) or yabs.selangor.gov.my.",
    amount_label="Free water + RM100–RM300/month depending on scheme",
    tags=["selangor", "state", "water"],
)

KL_AID = Scheme(
    id="kl_aid",
    name="Kuala Lumpur / Federal Territory Aid (YBSKL)",
    short_name="KL Aid",
    category="State",
    description=(
        "YBSKL (Yayasan Basmi Kemiskinan KL) provides monthly allowances, "
        "school assistance, rental aid, and skills training for KL/Putrajaya residents."
    ),
    how_to_apply="Apply at YBSKL office or dbkl.gov.my.",
    amount_label="RM300–RM600/month + rental/school supplements",
    tags=["KL", "federal territory", "state"],
)

ALL_SCHEMES: list[Scheme] = [
    STR, SOCSO_EIS, EPF_AKAUN3, MYSALAM, PEKA_B40,
    JKM_AID, BRIM_HISTORICAL, PTPTN_MORATORIUM, SELANGOR_AID, KL_AID,
]
