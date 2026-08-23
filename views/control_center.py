"""RevOps Director Control Center — Discovery-to-Handoff System Health.

Exception-first design: primary KPIs and an "Attention this week" panel answer
"What needs my attention?" before trends and deeper analytics.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components import metrics as m
from components import ui
from services import load_metrics, load_records, load_requirements, load_verticals

_PRIMARY_KPIS = ["first_pass_complete", "deals_critical_gaps", "clarification_rate", "median_time_to_handoff"]


def render() -> None:
    data = load_metrics()
    records = load_records()

    ui.page_header(
        "RevOps · Control center",
        "Discovery-to-handoff system health",
        "Know what you cannot afford to leave without knowing — at portfolio scale.",
    )
    st.markdown(
        f'<div class="faint small" style="margin-bottom:0.9rem;">As of {data["as_of_week"]} · mock operational data for this case study</div>',
        unsafe_allow_html=True,
    )

    df = _filtered_records(records)
    filtered = any(
        st.session_state.get(k, "All") != "All"
        for k in ("cc_vertical", "cc_rep", "cc_region", "cc_size", "cc_from_week")
    )
    kpis = _compute_kpis(data, df, filtered)

    st.markdown('<div class="section-title">Primary metrics</div>', unsafe_allow_html=True)
    _render_primary_kpis(kpis)

    _render_attention(data)

    st.markdown('<div class="section-title" style="margin-top:1rem;">Segmentation</div>', unsafe_allow_html=True)
    _render_filters(records)
    st.markdown(
        f'<div class="faint small" style="margin-bottom:0.6rem;">'
        f'{st.session_state.get("cc_vertical","All")} · {st.session_state.get("cc_rep","All")} · '
        f'{st.session_state.get("cc_region","All")} · {st.session_state.get("cc_size","All")} · '
        f'from {st.session_state.get("cc_from_week","All")} · {len(df)} records</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title" style="margin-top:1rem;">Trends</div>', unsafe_allow_html=True)
    _render_trends(df)

    st.markdown('<div class="section-title" style="margin-top:1rem;">Where requirements fail</div>', unsafe_allow_html=True)
    _render_gap_analysis(df)

    st.markdown('<div class="section-title" style="margin-top:1rem;">Vertical performance</div>', unsafe_allow_html=True)
    _render_vertical(df)

    st.markdown('<div class="section-title" style="margin-top:1rem;">Rep / team view</div>', unsafe_allow_html=True)
    _render_reps(df)

    st.markdown('<div class="section-title" style="margin-top:1rem;">Governed requirements</div>', unsafe_allow_html=True)
    _render_governance(data)

    st.markdown('<div class="section-title" style="margin-top:1rem;">What I would investigate this week</div>',
                unsafe_allow_html=True)
    _render_insights(data)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="foot">The control center exists so leadership can see whether governed requirements are '
        'creating measurable operational value — and where the playbook should evolve next.</div>',
        unsafe_allow_html=True,
    )


def _render_primary_kpis(kpis: dict) -> None:
    items = []
    for k in _PRIMARY_KPIS:
        v = kpis[k]
        val = v["value"]
        unit = v.get("unit", "")
        prev = v.get("prev")
        target = v.get("target")
        sep = "" if unit in ("", "%") else " "
        display = f"{val:g}{sep}{unit}"
        trend = m._trend_label(k, prev, val)
        color = ui.INK
        if target is not None:
            lower_better = k in m.LOWER_IS_BETTER
            good = (val >= target) if not lower_better else (val <= target)
            color = ui.GREEN if good else ui.AMBER
        sub = f"target {target:g}{sep}{unit}" if target is not None else ""
        items.append(m.kpi_card(k.replace("_", " ").title(), display, trend, color, sub))
    st.markdown(f'<div class="kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)
    st.write("")


def _render_attention(data: dict) -> None:
    st.markdown('<div class="section-title" style="margin-top:0.9rem;">Attention this week</div>', unsafe_allow_html=True)
    gap = data["missed_requirements"][0]
    trend_mark = "↑" if gap["trend"] == "up" else ("↓" if gap["trend"] == "down" else "→")
    vnames = load_verticals()
    vlabel = vnames.get(gap["vertical"], {}).get("name", gap["vertical"]) if gap["vertical"] != "all" else "All"
    st.markdown(
        f'<div class="attention">'
        f'<div class="attention-item">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem;">'
        f'<span style="font-weight:650; color:{ui.INK}; font-size:0.95rem;">{gap["requirement"]}</span>'
        f'<span class="chip chip-red">{gap["miss_rate"]}% miss rate {trend_mark}</span>'
        f'</div>'
        f'<div class="small muted" style="margin:0.2rem 0;">{vlabel} · {gap["downstream_impact"]} downstream impact</div>'
        f'<div class="small" style="color:{ui.INK};">Recommended action: <b>{gap.get("action", gap["note"])}</b></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.write("")


def _filtered_records(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    vert = st.session_state.get("cc_vertical", "All")
    rep = st.session_state.get("cc_rep", "All")
    region = st.session_state.get("cc_region", "All")
    size = st.session_state.get("cc_size", "All")
    from_week = st.session_state.get("cc_from_week", "All")
    if vert != "All":
        df = df[df["vertical_label"] == vert]
    if rep != "All":
        df = df[df["rep"] == rep]
    if region != "All":
        df = df[df["region"] == region]
    if size == "1 location":
        df = df[df["size"] == 1]
    elif size == "2–5 locations":
        df = df[df["size"].between(2, 5)]
    elif size == "6+ locations":
        df = df[df["size"] >= 6]
    if from_week != "All":
        cutoff = df.loc[df["week_label"] == from_week, "week"].max()
        if pd.isna(cutoff):
            cutoff = "2026-08-23"
        df = df[df["week"] <= cutoff]
    return df.reset_index(drop=True)


def _compute_kpis(data: dict, df: pd.DataFrame, filtered: bool) -> dict:
    """KPI row reacts to an active filter; unfiltered view shows the configured
    narrative values so the story stays intact."""
    kpi = {k: dict(v) for k, v in data["kpi"].items()}
    if filtered and not df.empty:
        kpi["first_pass_complete"]["value"] = round(100 * df["first_pass"].mean())
        kpi["clarification_rate"]["value"] = round(100 * df["clarification"].mean())
        kpi["median_time_to_handoff"]["value"] = round(float(df["time_to_handoff"].median()), 1)
        kpi["deals_critical_gaps"]["value"] = int((df["critical_gaps"] > 0).sum())
        kpi["median_time_to_live"]["value"] = round(float(df["time_to_live"].median()))
    return kpi


def _render_filters(records: list[dict]) -> None:
    data = load_metrics()
    verticals = ["All"] + [v["label"] for v in data["vertical_performance"]]
    reps = ["All"] + [r["rep"] for r in data["rep_performance"]]
    regions = ["All", "Northeast", "Southeast", "Midwest", "Southwest", "West", "Texas"]
    sizes = ["All", "1 location", "2–5 locations", "6+ locations"]
    week_map = {r["week_label"]: r["week"] for r in records}
    weeks = ["All"] + [label for label, _ in sorted(week_map.items(), key=lambda kv: kv[1])]

    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    with c1:
        st.selectbox("Vertical", verticals, key="cc_vertical")
    with c2:
        st.selectbox("Sales rep", reps, key="cc_rep")
    with c3:
        st.selectbox("Region", regions, key="cc_region")
    with c4:
        st.selectbox("Merchant size", sizes, key="cc_size")
    with c5:
        st.selectbox("Week", weeks, key="cc_from_week")
    st.write("")


def _render_trends(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No records match the current filters.")
        return
    weekly = (
        df.groupby(["week_label"])
        .agg(
            first_pass=("first_pass", "mean"),
            clarification=("clarification", "mean"),
            time_to_handoff=("time_to_handoff", "median"),
            reengagement=("reengagement", "mean"),
            time_to_live=("time_to_live", "median"),
            deals=("id", "count"),
        )
        .reset_index()
    )
    order = df.groupby("week_label")["week"].max().sort_values().index.tolist()
    weekly["_order"] = weekly["week_label"].map({w: i for i, w in enumerate(order)})
    weekly = weekly.sort_values("_order").drop(columns="_order")

    weekly["first_pass"] = (weekly["first_pass"] * 100).round(0)
    weekly["clarification"] = (weekly["clarification"] * 100).round(0)
    weekly["reengagement"] = (weekly["reengagement"] * 100).round(0)
    weekly["time_to_handoff"] = weekly["time_to_handoff"].round(1)
    weekly["time_to_live"] = weekly["time_to_live"].round(0)
    weekly["deals"] = weekly["deals"].astype(int)
    weekly = weekly.rename(columns={"week_label": "label"})
    st.caption(f"{weekly['deals'].sum()} submitted discoveries in this view")
    w = weekly.to_dict("records")

    c1, c2 = st.columns(2, gap="small")
    with c1:
        m.trend_chart(w, "first_pass", "First-pass completeness (%)", "%")
    with c2:
        m.trend_chart(w, "clarification", "Clarification / rework (%)", "%")

    c3, c4 = st.columns(2, gap="small")
    with c3:
        m.trend_chart(w, "time_to_handoff", "Time to handoff (days)", "days")
    with c4:
        m.trend_chart(w, "reengagement", "Rep re-engagement after handoff (%)", "%")

    m.trend_chart(w, "time_to_live", "Time to live (days)", "days")


def _render_gap_analysis(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No records match the current filters.")
        return
    data = load_metrics()
    vnames = load_verticals()
    def _vlabel(key: str) -> str:
        if key == "all":
            return "All"
        return vnames.get(key, {}).get("name", key)
    rows = []
    for item in data["missed_requirements"]:
        trend_mark = "↑" if item["trend"] == "up" else ("↓" if item["trend"] == "down" else "→")
        rows.append(
            f'<div class="row" style="padding:0.5rem 1rem;">'
            f'<span style="flex:1; min-width:0;"><b style="font-size:0.9rem;">{item["requirement"]}</b>'
            f'<div class="faint small">{item["note"]}</div></span>'
            f'<span style="display:flex; gap:0.5rem; align-items:center; flex-shrink:0;">'
            f'<span class="chip chip-neutral">{_vlabel(item["vertical"])}</span>'
            f'{m.severity_badge(item["downstream_impact"])}'
            f'<span class="chip chip-red">{item["miss_rate"]}% {trend_mark}</span></span></div>'
        )
    st.markdown(
        f'<div class="panel-flush" style="margin-bottom:0.8rem;">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )
    dfm = pd.DataFrame(data["missed_requirements"])
    m.bar_chart(dfm, "requirement", "miss_rate", "Miss rate by requirement (%)",
                color_col="downstream_impact",
                colors=["#B42318", "#B7791F", "#2F5FA8", "#B42318", "#B42318", "#B7791F", "#B7791F"])


def _render_vertical(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No records match the current filters.")
        return
    vdf = (
        df.groupby(["vertical_label"])
        .agg(
            deals=("id", "count"),
            first_pass=("first_pass", "mean"),
            clarification=("clarification", "mean"),
            time_to_handoff=("time_to_handoff", "median"),
            time_to_live=("time_to_live", "median"),
        )
        .reset_index()
        .rename(columns={
            "vertical_label": "Vertical", "deals": "Deals",
            "first_pass": "First-pass %", "clarification": "Clarification %",
            "time_to_handoff": "Time to handoff (d)", "time_to_live": "Time to live (d)",
        })
    )
    vdf["First-pass %"] = (vdf["First-pass %"] * 100).round(0)
    vdf["Clarification %"] = (vdf["Clarification %"] * 100).round(0)
    st.dataframe(vdf, hide_index=True, width="stretch")

    c1, c2 = st.columns(2, gap="small")
    with c1:
        m.bar_chart(vdf, "Vertical", "First-pass %", "First-pass completeness by vertical (%)")
    with c2:
        m.bar_chart(vdf, "Vertical", "Clarification %", "Clarification rate by vertical (%)")


def _render_reps(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No records match the current filters.")
        return
    st.markdown(
        '<div class="faint small" style="margin-bottom:0.5rem;">Framed as operational coaching — trends highlight '
        'where to reinforce the playbook, not to punish individuals.</div>',
        unsafe_allow_html=True,
    )
    rdf = (
        df.groupby(["rep"])
        .agg(
            deals=("id", "count"),
            first_pass=("first_pass", "mean"),
            critical_gaps=("critical_gaps", "sum"),
            clarification=("clarification", "mean"),
            time_to_handoff=("time_to_handoff", "median"),
        )
        .reset_index()
    )
    rdf["First-pass %"] = (rdf["first_pass"] * 100).round(0)
    rdf["Critical gap %"] = (100 * rdf["critical_gaps"] / rdf["deals"].clip(lower=1)).round(0)
    rdf["Clarification %"] = (rdf["clarification"] * 100).round(0)
    rdf["Time to handoff (d)"] = rdf["time_to_handoff"].round(1)
    disp = rdf.rename(columns={"rep": "Rep", "deals": "Deals"})[
        ["Rep", "Deals", "First-pass %", "Critical gap %", "Clarification %", "Time to handoff (d)"]]
    st.dataframe(disp, hide_index=True, width="stretch")
    m.bar_chart(rdf, "rep", "First-pass %", "First-pass completeness by rep (%)")


def _render_governance(data: dict) -> None:
    verticals = load_verticals()
    vnames = {k: v["name"] for k, v in verticals.items()}
    options = ["All"] + list(vnames.values())
    sel = st.selectbox("Filter requirements by vertical", options, key="gov_vertical")
    sel_key = None
    if sel != "All":
        sel_key = next((k for k, v in vnames.items() if v == sel), None)

    reqs = load_requirements()
    rows = []
    for r in reqs:
        if sel_key is not None and r.get("vertical") not in ("all", sel_key):
            continue
        prio = "critical" if r.get("priority") == "critical" else "important"
        badge = ui.status_badge(prio)
        rows.append(
            f'<div class="row" style="padding:0.45rem 1rem;">'
            f'<span style="flex:1; min-width:0;"><b style="font-size:0.88rem;">{r["label"]}</b>'
            f'<div class="faint small">{r.get("rule", "")} · Owner: {r.get("owner", "")} · {r.get("version", "")}</div></span>'
            f'<span style="display:flex; gap:0.5rem; align-items:center; flex-shrink:0;">'
            f'<span class="chip chip-neutral">{r.get("vertical") if r.get("vertical") != "all" else "All"}</span>'
            f'<span class="{badge}">{prio.title()}</span>'
            f'<span class="faint small">{r.get("last_updated", "")}</span></span></div>'
        )
    st.markdown(f'<div class="panel-flush" style="margin-bottom:0.6rem;">{"".join(rows)}</div>', unsafe_allow_html=True)

    if st.button("Edit requirement (mock)", width="content"):
        st.markdown(
            '<div class="panel" style="margin-top:0.6rem;"><div class="section-title">Edit requirement</div>'
            '<div class="small muted">This is a prototype — editing persists only for this session and represents '
            'the change-control workflow leadership would use to evolve the playbook.</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title" style="margin-top:0.8rem;">Governance activity (recent)</div>',
                unsafe_allow_html=True)
    for ev in data["governance_events"][::-1]:
        st.markdown(
            f'<div class="attention" style="border-left-color:{ui.ACCENT}; padding:0.55rem 0.85rem; margin-bottom:0.5rem;">'
            f'<span class="faint small">{ev["date"]} · {ev["owner"]}</span><div style="font-size:0.88rem;">{ev["change"]}</div></div>',
            unsafe_allow_html=True,
        )


def _render_insights(data: dict) -> None:
    for note in data["insights"]:
        st.markdown(
            f'<div class="attention" style="border-left-color:{ui.ACCENT}; padding:0.6rem 0.85rem; margin-bottom:0.5rem;">'
            f'<div style="font-size:0.88rem; color:{ui.INK};">{note}</div></div>',
            unsafe_allow_html=True,
        )
