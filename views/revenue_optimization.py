"""Revenue Optimization Plan — Director decision workspace.

SEE → UNDERSTAND → COMPARE → DECIDE → ACT
"""
from __future__ import annotations

import streamlit as st

from components import ui
from services import ai_service
from services.optimization import (
    add_decision,
    annual_opportunity,
    assumption_lines,
    build_project_plan,
    friction_score,
    get_driver,
    get_history,
    load_drivers,
    money,
    option_impact,
    ranked_drivers,
    render_plan_markdown,
)

_DISCLAIMER = (
    "Financial impact is illustrative and based on fictional case-study assumptions. "
    "Production estimates would be calibrated against Toast historical deal, implementation, "
    "and revenue data."
)


def _init_state() -> None:
    st.session_state.setdefault("opt_driver", None)
    st.session_state.setdefault("opt_option", None)
    st.session_state.setdefault("opt_sent", False)


def _dismiss() -> None:
    st.session_state["opt_driver"] = None
    st.session_state["opt_option"] = None
    st.session_state["opt_sent"] = False


def render() -> None:
    _init_state()

    ui.page_header(
        "RevOps · Revenue optimization",
        "Revenue Optimization Plan",
        "Prioritize the discovery improvements with the greatest potential business impact.",
    )

    if st.session_state.get("opt_driver"):
        _render_detail()
        return

    _render_landing()


# ---------------------------------------------------------------------------
# Landing: Top 10 Revenue Friction Drivers
# ---------------------------------------------------------------------------

def _render_landing() -> None:
    verticals = ["All", "Convenience + Fuel", "Independent Grocery", "Meat & Seafood",
                 "Specialty Food", "General Retail"]
    col, _ = st.columns([2, 4])
    with col:
        selected = st.selectbox("Vertical", verticals, key="opt_vertical")

    drivers = ranked_drivers(selected)
    st.markdown('<div class="section-title" style="margin-top:0.9rem;">Top Revenue Friction Drivers</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.82rem; margin-bottom:0.5rem;">Ranked by modeled friction opportunity '
        '(frequency × downstream consequence × affected deal volume), not miss rate alone.</div>',
        unsafe_allow_html=True,
    )

    for d in drivers:
        _driver_row(d)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="foot">{_DISCLAIMER}</div>', unsafe_allow_html=True)


def _driver_row(d: dict) -> None:
    score = friction_score(d)
    opp = annual_opportunity(d)
    impact = d["downstream_impact"] if "downstream_impact" in d else ("High" if score > 1500 else "Medium")
    vname = d["vertical_label"]

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:0.5rem; padding:0.7rem 1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;">
                <div style="flex:1; min-width:0;">
                    <span style="font-weight:650; font-size:0.98rem; color:{ui.INK};">{d['requirement']}</span>
                    <span class="chip chip-neutral">{vname}</span>
                </div>
                <div style="display:flex; align-items:center; gap:1.2rem; flex-shrink:0;">
                    <span class="muted small">{d['miss_rate']*100:.0f}% miss rate</span>
                    <span class="chip chip-red">High downstream impact</span>
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    <div class="small" style="color:{ui.INK};">Estimated annual opportunity</div>
                    <div style="font-weight:700; font-size:1.05rem; color:{ui.INK};">{money(opp)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("View Optimization Options →", key=f"opt_open_{d['id']}", width="content"):
        st.session_state["opt_driver"] = d["id"]
        st.rerun()


# ---------------------------------------------------------------------------
# Detail: Current state + three options
# ---------------------------------------------------------------------------

def _render_detail() -> None:
    driver = get_driver(st.session_state["opt_driver"])
    if driver is None:
        _dismiss()
        st.rerun()

    if st.button("← Back to revenue drivers"):
        _dismiss()
        st.rerun()

    explanation = ai_service.explain_friction(driver)
    opp = annual_opportunity(driver)
    affected = round(driver["annual_deals"] * (1 - (1 - driver["miss_rate"]) * (1 - driver["rework_probability"])))

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:1rem; padding:1rem 1.15rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1.5rem; flex-wrap:wrap;">
                <div>
                    <div class="eyebrow">Revenue optimization · friction driver</div>
                    <div style="font-size:1.4rem; font-weight:700; letter-spacing:-0.02em; color:{ui.INK};">{driver['requirement']}</div>
                    <div class="muted small" style="margin-top:0.15rem;">{driver['vertical_label']}</div>
                </div>
                <div class="chip chip-red">High downstream impact</div>
            </div>
            <div class="small" style="margin-top:0.7rem; color:{ui.INK};">{explanation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Current state</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    metrics = [
        (f"{driver['miss_rate']*100:.0f}%", "First-pass miss rate"),
        (f"{driver['delay_days']} days", "Avg delay when missed"),
        (f"{affected}", "Deals estimated affected / yr"),
        (f"{money(opp)}", "Modeled annual opportunity"),
    ]
    for col, (val, label) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{val}</div></div>',
                unsafe_allow_html=True,
            )
    st.caption("Illustrative model using fictional case-study assumptions.")

    # Decision / confirmation or option selection
    if st.session_state.get("opt_sent"):
        _render_sent_state(driver)
        return

    if st.session_state.get("opt_option"):
        _render_confirmation(driver)
    else:
        _render_options(driver)


def _option_rank(d: dict, i: int) -> str:
    return f"OPTION {i + 1}"


def _render_options(driver: dict) -> None:
    st.markdown('<div class="section-title" style="margin-top:1rem;">Recommended approaches</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.82rem; margin-bottom:0.5rem;">Three distinct interventions — prevent, predict, '
        'or protect. Compare modeled impact and constraints before choosing.</div>',
        unsafe_allow_html=True,
    )

    for i, opt in enumerate(driver["options"]):
        impact = option_impact(driver, opt)
        cat = opt["category"].title()
        why = ai_service.explain_option(driver, opt)
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:0.6rem; padding:0.9rem 1.05rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                    <div style="flex:1; min-width:0;">
                        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                            <span class="eyebrow" style="margin:0;">{_option_rank(driver, i)} · {cat}</span>
                        </div>
                        <div style="font-weight:650; font-size:1.02rem; color:{ui.INK}; margin-top:0.15rem;">{opt['name']}</div>
                    </div>
                    <div style="text-align:right; flex-shrink:0;">
                        <div class="small muted">Estimated annual impact</div>
                        <div style="font-weight:700; font-size:1.15rem; color:{ui.GREEN};">{money(impact)}</div>
                    </div>
                </div>
                <div class="small" style="margin-top:0.5rem; color:{ui.INK};">{opt['proposed_solution']}</div>
                <div class="small muted" style="margin-top:0.35rem;">{why}</div>
                <div class="small" style="margin-top:0.6rem;">
                    <span class="chip chip-neutral">Effort: {opt['effort']}</span>
                    <span class="chip chip-neutral">Time to value: {opt['time_to_value']}</span>
                    <span class="chip chip-neutral">Miss-rate reduction: {opt['reduction_pp']}pp</span>
                </div>
                <details style="margin-top:0.5rem; font-size:0.82rem; color:{ui.INK};">
                    <summary style="cursor:pointer; font-weight:550;">Potential constraints</summary>
                    <ul style="margin:0.4rem 0 0 1.1rem;">{''.join(f'<li>{c}</li>' for c in opt['constraints'])}</ul>
                </details>
                <details style="margin-top:0.4rem; font-size:0.82rem; color:{ui.INK};">
                    <summary style="cursor:pointer; font-weight:550;">View assumptions</summary>
                    <ul style="margin:0.4rem 0 0 1.1rem;">{''.join(f'<li>{l}</li>' for l in assumption_lines(driver, opt))}</ul>
                </details>
                <div style="margin-top:0.7rem;">
                """,
            unsafe_allow_html=True,
        )
        if st.button("Select this approach", key=f"opt_select_{opt['id']}", width="stretch"):
            st.session_state["opt_option"] = opt["id"]
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)


def _render_confirmation(driver: dict) -> None:
    opt = next((o for o in driver["options"] if o["id"] == st.session_state["opt_option"]), None)
    if opt is None:
        st.session_state["opt_option"] = None
        st.rerun()
    impact = option_impact(driver, opt)

    st.markdown(
        f"""
        <div class="panel" style="border:1px solid #CBE7D8; background:#F3F9F5; margin-top:1rem; padding:1rem 1.1rem;">
            <div class="section-title" style="color:{ui.GREEN};">Proposed optimization</div>
            <div class="small" style="line-height:1.9;">
                <b>Requirement:</b> {driver['requirement']}<br>
                <b>Selected approach:</b> {opt['name']}<br>
                <b>Estimated annual impact:</b> {money(impact)}<br>
                <b>Expected improvement:</b> +{opt['reduction_pp']}pp first-pass discovery<br>
                <b>Primary constraint:</b> {opt['constraints'][0]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 2], gap="small")
    with c1:
        if st.button("Decline", width="stretch"):
            add_decision(st, driver, opt, "Declined")
            _dismiss()
            st.rerun()
    with c2:
        if st.button("Send Draft Project Plan via Email to Me", width="stretch", type="primary"):
            st.session_state["opt_sent"] = True
            st.session_state["opt_plan_ready"] = True
            add_decision(st, driver, opt, "Draft plan sent")
            st.rerun()


def _render_sent_state(driver: dict) -> None:
    opt = next((o for o in driver["options"] if o["id"] == st.session_state["opt_option"]), None)
    if opt is None:
        return
    impact = option_impact(driver, opt)

    st.success("**Draft project plan generated** — email prepared for RevOps Director (simulated).")
    st.markdown(
        f'<div class="note" style="margin:0.4rem 0 1rem 0;">✓ Email would be sent to the RevOps Director inbox '
        f'via a connected email service. For this prototype, sending is simulated.</div>',
        unsafe_allow_html=True,
    )

    plan = build_project_plan(driver, opt)
    narrative = ai_service.draft_plan_narrative(driver, opt, plan)
    markdown = render_plan_markdown(driver, opt, plan)

    if narrative:
        st.markdown(f'<div class="brief" style="margin-bottom:0.8rem;">{narrative}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Preview project plan</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:0.6rem; padding:0.9rem 1.1rem;">
            <div class="small" style="line-height:1.8;">
                <b>Opportunity.</b> {plan['opportunity']}<br><br>
                <b>Proposed intervention.</b> {plan['proposed_intervention']}<br><br>
                <b>Business case.</b> {' · '.join(f'{k}: {v}' for k, v in plan['business_case'].items())}<br><br>
                <b>Scope.</b> {plan['scope']}<br><br>
                <b>Workstreams.</b> {'; '.join(name for name, _ in plan['workstreams'])}<br><br>
                <b>Owners.</b> {', '.join(plan['owners'])}<br><br>
                <b>Success metrics.</b> {', '.join(plan['success_metrics'])}<br><br>
                <b>Risks.</b> {'; '.join(plan['risks'])}<br><br>
                <b>Pilot.</b> {plan['pilot']}<br><br>
                <b>Measurement window.</b> {plan['measurement_window']}<br><br>
                <b>Next decision.</b> {plan['next_decision']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Copy plan (plain text)"):
        st.code(markdown, language="markdown")

    if st.button("← Back to revenue drivers", width="content", key="opt_back_sent"):
        _dismiss()
        st.rerun()

    _render_history()


# ---------------------------------------------------------------------------
# Decision history
# ---------------------------------------------------------------------------

def _render_history() -> None:
    st.markdown('<div class="section-title" style="margin-top:1rem;">Optimization decisions</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.82rem; margin-bottom:0.5rem;">Recent Director decisions — recommendations '
        'persist so they do not disappear after review.</div>',
        unsafe_allow_html=True,
    )
    history = get_history(st)
    if history:
        rows = ""
        for h in history:
            status = "Draft plan sent" if h["status"] == "Draft plan sent" else h["status"]
            cls = "chip-green" if status == "Draft plan sent" else ("chip-amber" if status == "Under review" else "chip-neutral")
            rows += (
                f'<div class="row" style="padding:0.5rem 1rem;">'
                f'<span style="flex:1; min-width:0;"><b style="font-size:0.9rem;">{h["requirement"]}</b>'
                f'<div class="faint small">{h["vertical"]} · {h["date"]}</div></span>'
                f'<span style="flex:1; min-width:0;" class="small muted">{h["decision"]}</span>'
                f'<span class="small" style="width:90px; text-align:right; font-weight:600;">{h["impact"]}</span>'
                f'<span class="chip {cls}">{status}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="panel-flush">{"".join(rows)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="small muted">No decisions recorded yet.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="foot" style="margin-top:0.6rem;">{_DISCLAIMER}</div>', unsafe_allow_html=True)
