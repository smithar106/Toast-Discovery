"""Revenue Optimization Plan — deterministic decision-support core.

All financial calculation, ranking, and workflow state is deterministic Python.
AI (services/ai_service) may enhance recommendation language and project-plan
drafting, but never computes financial figures.

Friction Opportunity Score = frequency x downstream consequence x affected volume
  = miss_rate * rework_probability * delay_days * annual_deals

Annual opportunity (full resolution) =
  annual_deals * miss_rate * rework_probability * delay_days * estimated_daily_revenue

Per-option annual impact =
  annual_deals * (reduction_pp/100) * rework_probability * delay_days * estimated_daily_revenue
"""
from __future__ import annotations

from pathlib import Path

from services import load_metrics

OPT_DATA = Path(__file__).resolve().parent.parent / "data" / "optimization.json"

import json

_CACHE: dict | None = None


def load_optimization() -> dict:
    global _CACHE
    if _CACHE is None:
        with open(OPT_DATA, "r", encoding="utf-8") as fh:
            _CACHE = json.load(fh)
    return _CACHE


def load_drivers() -> list[dict]:
    return load_optimization()["drivers"]


def get_driver(driver_id: str) -> dict | None:
    for d in load_drivers():
        if d["id"] == driver_id:
            return d
    return None


def friction_score(driver: dict) -> float:
    """Deterministic, transparent prioritization score."""
    return (
        driver["miss_rate"]
        * driver["rework_probability"]
        * driver["delay_days"]
        * driver["annual_deals"]
    )


def annual_opportunity(driver: dict) -> float:
    return (
        driver["annual_deals"]
        * driver["miss_rate"]
        * driver["rework_probability"]
        * driver["delay_days"]
        * driver["estimated_daily_revenue"]
    )


def option_impact(driver: dict, option: dict) -> float:
    return (
        driver["annual_deals"]
        * (option["reduction_pp"] / 100)
        * driver["rework_probability"]
        * driver["delay_days"]
        * driver["estimated_daily_revenue"]
    )


def ranked_drivers(vertical: str = "All") -> list[dict]:
    drivers = load_drivers()
    if vertical != "All":
        # accept either the internal key (convenience_fuel) or its display label
        key = vertical
        for d in load_drivers():
            if d["vertical_label"] == vertical:
                key = d["vertical"]
                break
        # include this vertical's drivers plus the shared 'all' vertical ones
        drivers = [d for d in drivers if d["vertical"] in (key, "all")]
    return sorted(drivers, key=friction_score, reverse=True)


def money(value: float) -> str:
    """Rounded, non-false-precise currency like ~$85K."""
    if value >= 1_000_000:
        return f"~${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"~${round(value / 1000)}K"
    return f"~${round(value)}"


def assumption_lines(driver: dict, option: dict | None = None) -> list[str]:
    """Transparent 'view assumptions' breakdown."""
    lines = [
        f"Affected annual deals: {driver['annual_deals']}",
        f"First-pass miss rate: {driver['miss_rate'] * 100:.0f}%",
        f"Rework / clarification probability: {driver['rework_probability'] * 100:.0f}%",
        f"Average downstream delay when missed: {driver['delay_days']} days",
        f"Estimated daily revenue per affected merchant: ${driver['estimated_daily_revenue']:,}",
    ]
    lines.append(
        f"Modeled full annual opportunity: {money(annual_opportunity(driver))}"
        f" ({driver['annual_deals']} x {driver['miss_rate'] * 100:.0f}% x "
        f"{driver['rework_probability'] * 100:.0f}% x {driver['delay_days']}d x "
        f"${driver['estimated_daily_revenue']:,})"
    )
    if option:
        lines.append(
            f"Option impact ({option['name']}): {money(option_impact(driver, option))} "
            f"= expected {option['reduction_pp']}pp miss-rate reduction applied to the modeled opportunity."
        )
    return lines


# ---------------------------------------------------------------------------
# Project plan
# ---------------------------------------------------------------------------

_DEFAULT_SUCCESS_METRICS = [
    "First-pass discovery rate",
    "Requirement miss rate",
    "Clarification / rework rate",
    "Sales re-engagement after handoff",
    "Time to handoff",
    "Time to live",
]


def build_project_plan(driver: dict, option: dict) -> dict:
    """Deterministic draft project plan. AI may refine wording later."""
    current_rate = driver["miss_rate"] * 100
    target = max(0, current_rate - option["reduction_pp"])
    opp = option_impact(driver, option)
    full_opp = annual_opportunity(driver)

    workstreams = [
        ("Requirements / process design", "Update the governed requirement and the discovery playbook."),
        ("Sales enablement", "Brief reps on the new prompt or gate and the reasoning behind it."),
        ("Onboarding alignment", "Align the preflight / checkpoint behavior with onboarding workflows."),
        ("Measurement", "Instrument miss rate and delay before rollout to establish a baseline."),
    ]

    return {
        "opportunity": (
            f"{driver['requirement']} creates the largest modeled friction for {driver['vertical_label']} "
            f"merchants: a {current_rate:.0f}% first-pass miss rate with an average "
            f"{driver['delay_days']}-day downstream delay when missed. Today this represents an estimated "
            f"{money(full_opp)} of annual opportunity, concentrated in a small number of high-value deals."
        ),
        "proposed_intervention": option["name"],
        "business_case": {
            "Current first-pass rate": f"{current_rate:.0f}%",
            "Target improvement": f"-{option['reduction_pp']}pp (toward {target:.0f}%)",
            "Affected deal volume": f"{driver['annual_deals']} deals / year",
            "Expected go-live impact": f"-{driver['delay_days']} days delay avoided per recovered case",
            "Estimated annual financial opportunity": money(opp),
        },
        "scope": (
            f"Implement '{option['name']}' for {driver['vertical_label']}. Update the governed requirement "
            f"definition, the discovery playbook, and the affected workflow. Monitor miss rate and delay "
            f"for {driver['vertical_label']} merchants against the pre-intervention baseline."
        ),
        "workstreams": workstreams,
        "owners": ["RevOps", "Retail Sales", "Sales Engineering", "Onboarding", "Product / Systems"],
        "success_metrics": _DEFAULT_SUCCESS_METRICS,
        "risks": option["constraints"],
        "pilot": (
            f"Run a bounded {driver['vertical_label']} pilot (6–8 weeks, ~{max(3, round(driver['annual_deals'] * 0.2))} "
            f"merchants) before broad rollout to validate the miss-rate reduction and rep friction without "
            f"committing the whole vertical."
        ),
        "measurement_window": "6–8 weeks post-pilot start; compare against a 12-week trailing baseline.",
        "next_decision": (
            "After the pilot, decide whether to (1) roll out broadly, (2) adjust the requirement logic, or "
            "(3) pursue an additional intervention (e.g., a later-stage preflight) for remaining friction."
        ),
    }


def render_plan_markdown(driver: dict, option: dict, plan: dict) -> str:
    m = []
    m.append("# Revenue Optimization Project Plan")
    m.append(f"**Requirement:** {driver['requirement']} · **Vertical:** {driver['vertical_label']}")
    m.append("")
    m.append("## Opportunity")
    m.append(plan["opportunity"])
    m.append("")
    m.append("## Proposed Intervention")
    m.append(plan["proposed_intervention"])
    m.append("")
    m.append("## Business Case")
    for k, v in plan["business_case"].items():
        m.append(f"- **{k}:** {v}")
    m.append("")
    m.append("## Scope")
    m.append(plan["scope"])
    m.append("")
    m.append("## Workstreams")
    for name, desc in plan["workstreams"]:
        m.append(f"- **{name}** — {desc}")
    m.append("")
    m.append("## Owners / Stakeholders")
    m.append(", ".join(plan["owners"]))
    m.append("")
    m.append("## Success Metrics")
    m.append(", ".join(plan["success_metrics"]))
    m.append("")
    m.append("## Risks / Constraints")
    for r in plan["risks"]:
        m.append(f"- {r}")
    m.append("")
    m.append("## Proposed Pilot")
    m.append(plan["pilot"])
    m.append("")
    m.append("## Measurement Window")
    m.append(plan["measurement_window"])
    m.append("")
    m.append("## Next Decision")
    m.append(plan["next_decision"])
    m.append("")
    m.append("---")
    m.append("_Illustrative draft based on fictional case-study assumptions. Not actual Toast financial data._")
    return "\n".join(m)


# ---------------------------------------------------------------------------
# Decision history
# ---------------------------------------------------------------------------

def _seed_history() -> list[dict]:
    return [
        {
            "requirement": "Age Verification",
            "vertical": "Convenience + Fuel",
            "decision": "Strengthen Playbook",
            "impact": money(option_impact(get_driver("age_verification"), get_driver("age_verification")["options"][0])),
            "status": "Draft plan sent",
            "date": "2026-08-18",
        },
        {
            "requirement": "Scale / Labeling",
            "vertical": "Independent Grocery",
            "decision": "Pre-qualify",
            "impact": money(option_impact(get_driver("scale_labeling"), get_driver("scale_labeling")["options"][1])),
            "status": "Under review",
            "date": "2026-08-12",
        },
        {
            "requirement": "Hardware Sizing",
            "vertical": "General Retail",
            "decision": "Declined",
            "impact": "—",
            "status": "Closed",
            "date": "2026-08-05",
        },
    ]


def get_history(st) -> list[dict]:
    if "opt_history" not in st.session_state:
        st.session_state["opt_history"] = _seed_history()
    return st.session_state["opt_history"]


def add_decision(st, driver: dict, option: dict, status: str) -> None:
    history = get_history(st)
    entry = {
        "requirement": driver["requirement"],
        "vertical": driver["vertical_label"],
        "decision": option["name"],
        "impact": money(option_impact(driver, option)),
        "status": status,
        "date": "2026-08-23",
    }
    history.insert(0, entry)
    st.session_state["opt_history"] = history
