"""Shared visual system — production internal-tool aesthetic.

Restrained warm accent, high information density, typography over containers.
"""
from __future__ import annotations

import streamlit as st

ACCENT = "#D94F2B"          # warm terracotta
ACCENT_HOVER = "#C4461F"
ACCENT_SOFT = "#FBEFE9"     # washed accent
INK = "#1A1D21"             # near-black text
MUTED = "#1A1D21"           # secondary text (black — no grey in this UI)
FAINT = "#1A1D21"           # tertiary text (black)
BORDER = "#E4E6E8"          # hairline
BORDER_STRONG = "#D4D7DA"
BG = "#F7F7F5"              # app background
BG_SOFT = "#F2F2F0"
CARD = "#FFFFFF"
GREEN = "#2F7D57"
GREEN_SOFT = "#EAF4EE"
AMBER = "#B07A1E"
AMBER_SOFT = "#FAF3E3"
RED = "#B42318"
RED_SOFT = "#FBEDEB"
BLUE = "#2F5FA8"
BLUE_SOFT = "#EAF1FA"


def apply_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700&display=swap');

        :root {{
            --accent: {ACCENT};
            --ink: {INK};
            --muted: {MUTED};
            --border: {BORDER};
        }}

        /* ---- Streamlit chrome cleanup ---- */
        [data-testid="stHeader"] {{ background: transparent; height: 0; min-height: 0; overflow: hidden; padding: 0; }}
        #MainMenu, footer {{ visibility: hidden; height: 0; }}
        [data-testid="stToolbar"] {{ display: none !important; }}
        [data-testid="stDecoration"] {{ display: none; }}
        .stAppDeployButton, [data-testid="stAppDeployButton"] {{ display: none !important; }}
        [data-testid="stStatusWidget"] {{ display: none; }}
        [data-testid="stToolbarInner"] {{ display: none; }}
        header[data-testid="stHeader"] div {{ min-height: 0 !important; }}

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
            color: {INK};
            font-size: 14px;
            line-height: 1.45;
        }}
        [data-testid="stAppViewContainer"] {{ background: {BG}; }}
        [data-testid="stAppViewBlockContainer"] {{ padding-top: 1.25rem; padding-bottom: 3rem; }}
        [data-testid="stSidebar"] {{
            background: #FBFAF8;
            border-right: 1px solid {BORDER};
            min-width: 260px;
        }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ padding-top: 0.75rem; }}

        .block-container {{ max-width: 1180px; }}

        /* ---- Typography ---- */
        h1 {{ font-size: 1.55rem; font-weight: 650; letter-spacing: -0.02em; color: {INK}; margin-bottom: 0.1rem; }}
        h2 {{ font-size: 1.15rem; font-weight: 600; letter-spacing: -0.01em; color: {INK}; }}
        h3 {{ font-size: 1rem; font-weight: 600; color: {INK}; }}
        p {{ margin-bottom: 0.25rem; }}
        .eyebrow {{ font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase; color: {FAINT}; font-weight: 600; margin-bottom: 0.15rem; }}
        .muted {{ color: {MUTED}; }}
        .faint {{ color: {FAINT}; }}
        .small {{ font-size: 0.82rem; }}
        .section-title {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: {INK}; margin: 0 0 0.4rem 0; }}
        .divider {{ border-top: 1px solid {BORDER}; margin: 1rem 0; }}

        /* ---- Panels (typography-led, minimal borders) ---- */
        .panel {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0.85rem 1rem; }}
        .panel-flush {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; }}
        .row {{ display: flex; align-items: center; gap: 0.85rem; padding: 0.55rem 1rem; }}
        .row + .row {{ border-top: 1px solid #EFF0F1; }}
        .row:hover {{ background: #FAFAF9; }}

        /* ---- Agenda rows ---- */
        .agenda-time {{ font-size: 0.95rem; font-weight: 600; color: {INK}; min-width: 58px; white-space: nowrap; }}
        .agenda-name {{ font-weight: 600; font-size: 0.95rem; color: {INK}; }}
        .agenda-meta {{ font-size: 0.78rem; color: {MUTED}; }}
        .agenda-arrow {{ color: {FAINT}; font-size: 1rem; }}

        /* ---- Playbook compact rows ---- */
        .q-row {{ display: flex; align-items: center; gap: 0.9rem; padding: 0.5rem 1rem; }}
        .q-row + .q-row {{ border-top: 1px solid #EFF0F1; }}
        .q-text {{ flex: 1; min-width: 0; }}
        .q-label {{ font-size: 0.9rem; font-weight: 500; color: {INK}; }}
        .q-help {{ font-size: 0.75rem; color: {FAINT}; margin-top: 0.1rem; }}

        /* ---- Status chips (restrained) ---- */
        .chip {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.12rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-weight: 550; letter-spacing: 0.01em; white-space: nowrap; }}
        .chip-neutral {{ background: {BG_SOFT}; color: {MUTED}; border: 1px solid {BORDER}; }}
        .chip-accent {{ background: {ACCENT_SOFT}; color: {ACCENT}; border: 1px solid transparent; }}
        .chip-green {{ background: {GREEN_SOFT}; color: {GREEN}; border: 1px solid transparent; }}
        .chip-amber {{ background: {AMBER_SOFT}; color: {AMBER}; border: 1px solid transparent; }}
        .chip-red {{ background: {RED_SOFT}; color: {RED}; border: 1px solid transparent; }}
        .chip-blue {{ background: {BLUE_SOFT}; color: {BLUE}; border: 1px solid transparent; }}
        .chip-ghost {{ background: transparent; color: {MUTED}; border: 1px solid {BORDER_STRONG}; }}

        .status-dot {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; }}

        /* ---- Critical panel ---- */
        .critical-header {{ display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.6rem 1rem; background: {RED_SOFT}; border-bottom: 1px solid #F2D8D4; border-radius: 8px 8px 0 0; }}
        .critical-title {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: {RED}; }}
        .important-header {{ display: flex; align-items: center; justify-content: space-between; padding: 0.55rem 1rem; background: {AMBER_SOFT}; border-bottom: 1px solid #EFE3C8; border-radius: 8px 8px 0 0; }}
        .important-title {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: {AMBER}; }}

        /* ---- Insight / brief ---- */
        .brief {{ background: {CARD}; border: 1px solid {BORDER}; border-left: 3px solid {ACCENT}; border-radius: 6px; padding: 0.65rem 0.85rem; }}
        .brief-title {{ font-size: 0.72rem; font-weight: 650; letter-spacing: 0.06em; text-transform: uppercase; color: {MUTED}; margin-bottom: 0.15rem; }}
        .attention {{ background: {CARD}; border: 1px solid {BORDER}; border-left: 3px solid {AMBER}; border-radius: 6px; padding: 0.65rem 0.85rem; }}
        .attention-item {{ border-bottom: 1px solid #EFF0F1; padding: 0.45rem 0; }}
        .attention-item:last-child {{ border-bottom: none; padding-bottom: 0; }}
        .attention-item:first-child {{ padding-top: 0; }}

        /* ---- Metrics / KPI ---- */
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0.6rem; }}
        .kpi-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0.7rem 0.85rem; }}
        .kpi-card .kpi-label {{ font-size: 0.68rem; letter-spacing: 0.07em; text-transform: uppercase; color: {FAINT}; font-weight: 600; }}
        .kpi-card .kpi-value {{ font-size: 1.5rem; font-weight: 650; letter-spacing: -0.02em; color: {INK}; line-height: 1.15; }}
        .kpi-card .kpi-sub {{ font-size: 0.72rem; color: {FAINT}; margin-top: 0.05rem; }}
        .kpi {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0.7rem 0.85rem; }}
        .kpi-label {{ font-size: 0.68rem; letter-spacing: 0.07em; text-transform: uppercase; color: {FAINT}; font-weight: 600; }}
        .kpi-value {{ font-size: 1.5rem; font-weight: 650; letter-spacing: -0.02em; color: {INK}; line-height: 1.15; }}
        .kpi-sub {{ font-size: 0.72rem; color: {FAINT}; margin-top: 0.05rem; }}

        /* ---- Misc ---- */
        .note {{ background: {ACCENT_SOFT}; border-left: 3px solid {ACCENT}; border-radius: 6px; padding: 0.6rem 0.85rem; font-size: 0.85rem; color: #7A3A1E; }}
        .foot {{ font-size: 0.72rem; color: {FAINT}; }}
        .pill-row {{ display: flex; flex-wrap: wrap; gap: 0.35rem; }}

        /* ---- Streamlit control restyle ---- */
        [data-testid="stWidgetLabel"] p {{ font-size: 0.85rem; font-weight: 500; color: {INK}; }}
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
            font-size: 0.88rem; border-radius: 6px; border-color: {BORDER_STRONG};
        }}
        [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {{
            border-color: {ACCENT}; box-shadow: 0 0 0 1px {ACCENT};
        }}
        div[data-baseweb="select"] > div {{
            background: {CARD}; border-radius: 6px; border-color: {BORDER_STRONG};
        }}
        div[data-baseweb="select"] > div:hover {{ border-color: {BORDER_STRONG}; }}

        /* segmented control (Yes/No/Unknown) */
        [data-testid="stSegmentedControl"] {{
            background: {BG_SOFT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 2px;
        }}
        [data-testid="stSegmentedControl"] button {{
            border-radius: 4px; font-size: 0.8rem; font-weight: 500; padding: 0.25rem 0.9rem;
        }}
        [data-testid="stSegmentedControl"] button[aria-checked="true"] {{
            background: {CARD}; color: {INK}; box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }}

        /* radio */
        [data-testid="stRadio"] label span {{ font-size: 0.85rem; }}

        /* buttons */
        .stButton > button {{
            background: {INK}; color: #fff; border: none; border-radius: 6px;
            font-size: 0.83rem; font-weight: 550; padding: 0.4rem 0.9rem;
        }}
        .stButton > button:hover {{ background: #2E3238; color: #fff; border: none; }}
        .stButton > button[kind="primary"] {{
            background: {ACCENT}; color: #fff;
        }}
        .stButton > button[kind="primary"]:hover {{ background: {ACCENT_HOVER}; color: #fff; }}
        .stButton > button:disabled {{ background: {BG_SOFT}; color: {FAINT}; }}
        [data-testid="stFormSubmitButton"] > button {{
            background: {ACCENT}; color: #fff; border: none; border-radius: 6px;
            font-size: 0.83rem; font-weight: 550;
        }}
        [data-testid="stFormSubmitButton"] > button:hover {{ background: {ACCENT_HOVER}; color: #fff; }}

        /* primary action button full width */
        .stButton > button[data-testid="baseButton-primary"], .stButton > button[kind="primary"] {{
            width: 100%;
        }}

        /* expanders */
        [data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 6px; }}
        [data-testid="stExpander"] summary {{ font-size: 0.85rem; }}

        /* file uploader */
        [data-testid="stFileUploaderDropzone"] {{
            background: {BG_SOFT}; border: 1px dashed {BORDER_STRONG}; border-radius: 6px;
        }}
        [data-testid="stFileUploaderDropzone"] small {{ font-size: 0.8rem; }}

        /* dataframe */
        [data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 6px; font-size: 0.82rem; }}

        /* checkbox */
        [data-testid="stCheckbox"] label span {{ font-size: 0.82rem; }}

        /* caption */
        [data-testid="stCaptionContainer"] p {{ font-size: 0.78rem; color: {FAINT}; }}

        /* metric */
        [data-testid="stMetric"] {{
            background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0.6rem 0.8rem;
        }}
        [data-testid="stMetricLabel"] p {{ font-size: 0.72rem; }}
        [data-testid="stMetricValue"] {{ font-size: 1.4rem; }}

        /* success / warning / error */
        [data-testid="stAlert"] {{ border-radius: 6px; font-size: 0.85rem; }}
        [data-testid="stSuccess"] {{ background: {GREEN_SOFT}; border: 1px solid #CFE5D8; color: {GREEN}; }}
        [data-testid="stWarning"] {{ background: {AMBER_SOFT}; border: 1px solid #EFE3C8; color: {AMBER}; }}
        [data-testid="stError"] {{ background: {RED_SOFT}; border: 1px solid #F2D8D4; color: {RED}; }}
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


def chip(text: str, kind: str = "neutral") -> str:
    return f'<span class="chip chip-{kind}">{text}</span>'


def status_badge(status: str) -> str:
    styles = {
        "complete": "chip chip-green",
        "in_progress": "chip chip-amber",
        "needs_attention": "chip chip-red",
        "critical": "chip chip-red",
        "important": "chip chip-amber",
        "info": "chip chip-blue",
        "known": "chip chip-blue",
        "ai": "chip chip-accent",
        "confirmed": "chip chip-green",
        "submitted": "chip chip-blue",
    }
    return styles.get(status, "chip chip-neutral")
