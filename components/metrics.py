"""Control Center metrics + charts."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components import ui


LOWER_IS_BETTER = {
    "clarification", "time_to_handoff", "time_to_live",
    "reengagement", "deals_critical_gaps", "missed_requirements",
}


def _trend_label(metric: str, prev, value) -> str:
    if prev is None:
        return ""
    try:
        pv = float(prev)
        vv = float(value)
    except (TypeError, ValueError):
        return ""
    if vv == pv:
        return "flat vs prev week"
    delta = abs(vv - pv)
    lower_better = metric in LOWER_IS_BETTER
    improved = (vv < pv) if lower_better else (vv > pv)
    arrow = "↓" if vv < pv else "↑"
    tone = ui.GREEN if improved else ui.RED
    return f'<span style="color:{tone};">{arrow} {delta:g} vs prev wk</span>'


def kpi_card(label: str, value: str, trend: str, color: str = ui.INK, sub: str = "") -> str:
    color_html = f"color:{color};" if color else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="{color_html}">{value}</div>'
        f'<div class="kpi-sub">{trend}</div>'
        f'{"<div class=\"kpi-sub\">" + sub + "</div>" if sub else ""}'
        f'</div>'
    )


def render_kpi_row(kpis: dict) -> None:
    items = []
    for k, v in kpis.items():
        val = v["value"]
        unit = v.get("unit", "")
        prev = v.get("prev")
        target = v.get("target")
        sep = "" if unit in ("", "%") else " "
        display = f"{val:g}{sep}{unit}"
        trend = _trend_label(k, prev, val)
        color = ui.INK
        if target is not None:
            lower_better = k in LOWER_IS_BETTER
            good = (val >= target) if not lower_better else (val <= target)
            color = ui.GREEN if good else ui.AMBER
        sub = f"target {target:g}{sep}{unit}" if target is not None else ""
        items.append(kpi_card(k.replace("_", " ").title(), display, trend, color, sub))
    st.markdown(f'<div class="kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)
    st.write("")


def trend_chart(weekly: list[dict], metric_key: str, title: str, y_title: str) -> None:
    df = pd.DataFrame(weekly)
    fig = px.line(
        df, x="label", y=metric_key, title=title, markers=True,
        color_discrete_sequence=[ui.ACCENT],
    )
    fig.update_layout(
        height=280, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="Inter, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=14, color=ui.INK),
        yaxis_title=y_title, xaxis_title="",
        hovermode="x unified",
    )
    fig.update_traces(line_width=2.5, marker_size=6)
    st.plotly_chart(fig, width="stretch")


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color_col: str | None = None, colors: list[str] | None = None) -> None:
    fig = px.bar(
        df, x=x, y=y, title=title, color=color_col,
        color_discrete_sequence=colors or [ui.ACCENT],
        text=y,
    )
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="Inter, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=14, color=ui.INK),
        xaxis_title="", yaxis_title="",
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    st.plotly_chart(fig, width="stretch")


def severity_badge(impact: str) -> str:
    if impact == "High":
        return f'<span class="badge badge-red">High</span>'
    if impact == "Medium":
        return f'<span class="badge badge-amber">Medium</span>'
    return f'<span class="badge badge-blue">Low</span>'
