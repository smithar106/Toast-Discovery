"""Shared visual styling — restrained warm internal-tool aesthetic."""
from __future__ import annotations

import streamlit as st

ACCENT = "#E4542E"          # warm terracotta
ACCENT_SOFT = "#F7E8E1"     # washed accent
INK = "#1F2430"             # near-black text
MUTED = "#6B7280"           # secondary text
BORDER = "#E7E5E0"          # hairline
BG_SOFT = "#FBF9F7"         # warm off-white
GREEN = "#2E7D5B"
AMBER = "#B7791F"
RED = "#B42318"
BLUE = "#2563EB"


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', -apple-system, sans-serif;
            color: {INK};
        }}
        [data-testid="stAppViewContainer"] {{ background: {BG_SOFT}; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        .block-container {{ padding-top: 2rem; padding-bottom: 4rem; max-width: 1120px; }}
        h1 {{ color: {INK}; font-weight: 700; letter-spacing: -0.02em; }}
        h2 {{ color: {INK}; font-weight: 650; letter-spacing: -0.01em; }}
        h3 {{ color: {INK}; font-weight: 600; }}
        .eyebrow {{ font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: {MUTED}; font-weight: 600; }}
        .card {{ background: #ffffff; border: 1px solid {BORDER}; border-radius: 12px; padding: 1.1rem 1.2rem; box-shadow: 0 1px 2px rgba(16,24,40,0.04); }}
        .stat {{ background: #ffffff; border: 1px solid {BORDER}; border-radius: 12px; padding: 0.9rem 1.1rem; }}
        .stat-label {{ font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; color: {MUTED}; font-weight: 600; }}
        .stat-value {{ font-size: 1.7rem; font-weight: 700; color: {INK}; letter-spacing: -0.02em; line-height: 1.2; }}
        .stat-trend {{ font-size: 0.78rem; font-weight: 600; }}
        .badge {{ display:inline-block; padding: 0.14rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; border: 1px solid {BORDER}; color: {MUTED}; background:#fff; }}
        .badge-accent {{ background: {ACCENT_SOFT}; color: {ACCENT}; border-color: transparent; }}
        .badge-green {{ background: #E7F3EC; color: {GREEN}; border-color: transparent; }}
        .badge-amber {{ background: #FBF2E0; color: {AMBER}; border-color: transparent; }}
        .badge-red {{ background: #FBE9E7; color: {RED}; border-color: transparent; }}
        .badge-blue {{ background: #E8EFFE; color: {BLUE}; border-color: transparent; }}
        .pill-row {{ display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.5rem; }}
        .merchant-name {{ font-size: 1.02rem; font-weight: 650; color: {INK}; }}
        .muted {{ color: {MUTED}; }}
        .small {{ font-size: 0.82rem; }}
        .section-title {{ font-size: 0.95rem; font-weight: 650; color: {INK}; margin-bottom: 0.3rem; }}
        .req-card {{ background:#fff; border:1px solid {BORDER}; border-radius:10px; padding:0.9rem 1rem; margin-bottom:0.55rem; }}
        .req-question {{ font-weight:600; color:{INK}; font-size:0.93rem; }}
        .req-help {{ font-size:0.8rem; color:{MUTED}; margin-top:0.25rem; }}
        .divider {{ border-top:1px solid {BORDER}; margin: 1.2rem 0; }}
        .status-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }}
        .kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap:0.75rem; }}
        .kpi-card {{ background:#fff; border:1px solid {BORDER}; border-radius:12px; padding:0.85rem 1rem; }}
        .kpi-label {{ font-size:0.7rem; letter-spacing:0.06em; text-transform:uppercase; color:{MUTED}; font-weight:600; }}
        .kpi-value {{ font-size:1.45rem; font-weight:700; color:{INK}; letter-spacing:-0.02em; }}
        .kpi-sub {{ font-size:0.75rem; color:{MUTED}; }}
        .handoff-section {{ margin-bottom: 1rem; }}
        .handoff-row {{ display:flex; justify-content:space-between; gap:1rem; padding:0.35rem 0; border-bottom:1px solid #F1F0EC; font-size:0.88rem; }}
        .handoff-label {{ color:{MUTED}; }}
        .handoff-value {{ font-weight:500; text-align:right; }}
        .source-chip {{ font-size:0.68rem; color:{MUTED}; border:1px solid {BORDER}; padding:0.1rem 0.45rem; border-radius:999px; white-space:nowrap; }}
        .note {{ background:{ACCENT_SOFT}; border-left:3px solid {ACCENT}; border-radius:6px; padding:0.7rem 0.9rem; font-size:0.85rem; color:#7A3A1E; }}
        .insight {{ background:#fff; border:1px solid {BORDER}; border-left:3px solid {ACCENT}; border-radius:8px; padding:0.75rem 0.95rem; font-size:0.88rem; margin-bottom:0.6rem; }}
        .foot {{ font-size:0.75rem; color:{MUTED}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="muted small">{subtitle}</div>', unsafe_allow_html=True)
    st.write("")


def status_badge(status: str) -> str:
    styles = {
        "complete": "badge badge-green",
        "in_progress": "badge badge-amber",
        "needs_attention": "badge badge-red",
        "critical": "badge badge-red",
        "important": "badge badge-amber",
        "info": "badge badge-blue",
        "known": "badge badge-blue",
        "ai": "badge badge-accent",
        "confirmed": "badge badge-green",
    }
    return styles.get(status, "badge")
