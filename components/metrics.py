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


def trend_card(weekly: list[dict], metric_key: str, cfg: dict) -> None:
    """Causal-funnel trend card: directional title, value + delta since baseline,
    and a chart with a target reference line.

    cfg keys: label, unit, higher_better, target, stage (e.g. 'Discovery quality').
    """
    df = pd.DataFrame(weekly)
    values = df[metric_key].tolist()
    current = float(values[-1])
    baseline = float(values[0])
    delta = current - baseline
    unit = cfg.get("unit", "")
    sep = "" if unit in ("", "%") else " "
    display = f"{current:g}{sep}{unit}"

    target = cfg.get("target")
    higher_better = cfg.get("higher_better", True)
    direction = "↑" if higher_better else "↓"
    target_dir = "≥" if higher_better else "≤"

    good = (current >= target) if higher_better else (current <= target)
    delta_good = (delta > 0) if higher_better else (delta < 0)
    delta_color = ui.GREEN if delta_good else ui.RED
    delta_arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
    delta_pp = unit == "%"

    if delta_pp:
        delta_text = f"{delta_arrow} {abs(delta):g}pp since baseline"
    else:
        delta_text = f"{delta_arrow} {abs(delta):g} {unit} since baseline"

    stage = cfg.get("stage", "")
    value_color = ui.GREEN if good else ui.INK

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:0.6rem; padding:0.75rem 1rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.75rem; flex-wrap:wrap;">
                <div>
                    <div class="faint small" style="font-size:0.7rem; letter-spacing:0.07em; text-transform:uppercase; font-weight:600;">{stage}</div>
                    <div style="font-weight:650; font-size:0.98rem; color:{ui.INK}; margin-top:0.1rem;">
                        {cfg['label']} {direction} <span class="faint small">· {('Higher' if higher_better else 'Lower')} is better · Target {target_dir} {target:g}{sep}{unit}</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:700; font-size:1.35rem; color:{value_color};">{display}</span>
                    <div style="font-size:0.78rem; color:{delta_color}; font-weight:600;">{delta_text}</div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    fig = px.line(
        df, x="label", y=metric_key, markers=True,
        color_discrete_sequence=[ui.ACCENT],
    )
    if target is not None:
        fig.add_hline(
            y=target, line_dash="dash", line_color="#B9BEC4", line_width=1,
            annotation_text=f"target {target:g}{sep}{unit}",
            annotation_position="top left",
            annotation_font=dict(size=10, color="#8A9096"),
        )
    fig.update_layout(
        height=200, margin=dict(l=8, r=8, t=24, b=8),
        font=dict(family="Inter, sans-serif", size=11),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, yaxis_title="", xaxis_title="",
        hovermode="x unified",
    )
    fig.update_traces(line_width=2.2, marker_size=5)
    st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


def sparkline(weekly: list[dict], metric_key: str, cfg: dict) -> None:
    """Compact secondary chart (e.g. time to handoff): value + delta + tiny line."""
    df = pd.DataFrame(weekly)
    values = df[metric_key].tolist()
    current = float(values[-1])
    baseline = float(values[0])
    delta = current - baseline
    unit = cfg.get("unit", "")
    sep = "" if unit in ("", "%") else " "
    display = f"{current:g}{sep}{unit}"
    target = cfg.get("target")
    higher_better = cfg.get("higher_better", True)
    good = (current >= target) if higher_better else (current <= target)
    delta_good = (delta > 0) if higher_better else (delta < 0)
    delta_color = ui.GREEN if delta_good else ui.RED
    delta_arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
    delta_text = f"{delta_arrow} {abs(delta):g} {unit} vs baseline"
    value_color = ui.GREEN if good else ui.INK

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:0.6rem; padding:0.7rem 1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; flex-wrap:wrap;">
                <div>
                    <div style="font-weight:600; font-size:0.92rem; color:{ui.INK};">{cfg['label']} <span class="faint small">· Target {('≥' if higher_better else '≤')} {target:g}{sep}{unit}</span></div>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:700; font-size:1.15rem; color:{value_color};">{display}</span>
                    <span style="font-size:0.76rem; color:{delta_color}; font-weight:600; margin-left:0.4rem;">{delta_text}</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    fig = px.line(
        df, x="label", y=metric_key, markers=False,
        color_discrete_sequence=[ui.ACCENT],
    )
    if target is not None:
        fig.add_hline(y=target, line_dash="dash", line_color="#B9BEC4", line_width=1)
    fig.update_layout(
        height=110, margin=dict(l=8, r=8, t=10, b=8),
        font=dict(family="Inter, sans-serif", size=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, yaxis_title="", xaxis_title="", yaxis_visible=False,
    )
    fig.update_traces(line_width=2, fill="tozeroy", fillcolor="rgba(217,79,43,0.06)")
    st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


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
