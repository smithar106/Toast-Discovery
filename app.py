"""Toast Retail Discovery — entry point.

Run locally:
    streamlit run app.py

Two role-based experiences from one URL: Sales Rep (This Week / playbooks) and
RevOps Director (Control Center).
"""
from __future__ import annotations

import streamlit as st

from components import ui
from views import control_center, sales_rep

st.set_page_config(
    page_title="Toast Retail Discovery",
    page_icon="🥖",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.apply_theme()


def _init_state() -> None:
    if "role" not in st.session_state:
        st.session_state["role"] = "Sales Rep"
    if "rep_view" not in st.session_state:
        st.session_state["rep_view"] = "home"


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:0.2rem 0 0.6rem 0;">
                <div style="font-weight:700; font-size:1.05rem; color:{ui.INK};">
                    <span style="color:{ui.ACCENT};">Toast</span> Retail Discovery
                </div>
                <div class="eyebrow" style="margin-top:0.2rem;">Interview prototype</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        role = st.radio(
            "Experience",
            ["Sales Rep", "RevOps Director"],
            key="role",
            label_visibility="collapsed",
        )
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="muted small">Know what you cannot afford to leave without knowing.</div>',
            unsafe_allow_html=True,
        )
        if role == "Sales Rep":
            st.markdown(
                f'<div class="badge badge-accent" style="margin-top:0.6rem;">Rep: Maya Chen</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="badge badge-blue" style="margin-top:0.6rem;">RevOps Director</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="foot">All merchant data is fictional mock data created for this case study. '
            'LLM features are optional; the demo runs fully offline.</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    _init_state()
    _sidebar()

    if st.session_state["role"] == "Sales Rep":
        sales_rep.render()
    else:
        control_center.render()


if __name__ == "__main__":
    main()
