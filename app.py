"""Toast Retail Discovery — entry point.

Run locally:
    streamlit run app.py

Two role-based experiences from one URL: Sales Rep (discovery agenda / playbooks)
and RevOps Director (control center).
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
        st.session_state["role"] = "Sales"
    if "rep_view" not in st.session_state:
        st.session_state["rep_view"] = "home"


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:0.2rem 0 0.9rem 0;">
                <div style="font-weight:700; font-size:1.1rem; letter-spacing:-0.02em; color:{ui.INK};">
                    <span style="color:{ui.ACCENT};">Toast</span> Retail
                </div>
                <div class="faint" style="font-size:0.78rem;">Discovery · Sales intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-title">Workspace</div>', unsafe_allow_html=True)
        role = st.radio(
            "Workspace",
            ["Sales", "RevOps"],
            key="role",
            label_visibility="collapsed",
        )
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if role == "Sales":
            st.markdown(
                f'<div class="chip chip-accent">Rep · Maya Chen</div><div style="height:0.4rem;"></div>'
                f'<div class="faint small">Northeast</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chip chip-blue">RevOps Director</div><div style="height:0.4rem;"></div>'
                f'<div class="faint small">System health</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="faint small">Know what you cannot afford to leave without knowing.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="foot" style="margin-top:1rem;">Demo data is fictional and created for this case study.</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    _init_state()
    _sidebar()

    if st.session_state["role"] == "Sales":
        sales_rep.render()
    else:
        control_center.render()


if __name__ == "__main__":
    main()
