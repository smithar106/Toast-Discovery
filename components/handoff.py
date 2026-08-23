"""Onboarding handoff artifact rendering."""
from __future__ import annotations

import streamlit as st

from components import ui
from services.handoff_service import build_handoff


def _rows(items: list[dict]) -> str:
    html = []
    for item in items:
        src = item.get("source", "")
        chip = f'<span class="source-chip">{src}</span>' if src and src != "Not captured" else ""
        html.append(
            f'<div class="handoff-row"><span class="handoff-label">{item["label"]}</span>'
            f'<span style="display:flex;gap:0.5rem;align-items:center;"><span class="handoff-value">{item["value"]}</span>{chip}</span></div>'
        )
    return "".join(html)


def render_handoff(merchant: dict, answers: dict, notes: str = "", summary: str = "") -> None:
    handoff = build_handoff(merchant, answers, notes, summary)

    st.markdown(
        f"""
        <div class="card" style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div class="eyebrow">Onboarding handoff · {handoff['meeting_date']}</div>
                    <div style="font-size:1.15rem; font-weight:700; color:{ui.INK}; margin-top:0.2rem;">{handoff['merchant']}</div>
                    <div class="muted small">{handoff['vertical']} · {handoff['locations']} location(s) · {handoff['region']} · ${handoff['opportunity_value']:,}</div>
                </div>
                <span class="badge badge-green">Ready for onboarding</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Merchant overview</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;">{_rows([{"label": k, "value": v} for k, v in handoff["overview"].items()])}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Critical implementation requirements</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;">{_rows(handoff["critical"])}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Integrations &amp; hardware / important context</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;">{_rows(handoff["important"])}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Merchant priorities &amp; context</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;">{_rows(handoff["known_context"])}</div>',
        unsafe_allow_html=True,
    )

    if handoff.get("open_questions"):
        st.markdown('<div class="section-title">Open questions (non-blocking)</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card" style="margin-bottom:1rem;">{_rows(handoff["open_questions"])}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Additional context (rep notes)</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;"><div style="font-size:0.88rem; color:{ui.INK};">{handoff["notes"]}</div></div>',
        unsafe_allow_html=True,
    )

    if handoff.get("summary"):
        st.markdown('<div class="section-title">Discovery summary</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="card" style="margin-bottom:1rem;"><div style="font-size:0.88rem; color:{ui.INK};">{handoff["summary"]}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Information provenance</div>', unsafe_allow_html=True)
    src_html = "".join(
        f'<span class="badge badge-blue" style="margin-right:6px;">{label}: {count}</span>'
        for label, count in handoff["sources"].items()
    )
    st.markdown(
        f'<div class="card"><div class="muted small" style="margin-bottom:0.4rem;">Every field traces to its source:</div>{src_html}'
        f'<div class="foot" style="margin-top:0.6rem;">Structured upstream discovery keeps the onboarding handoff deterministic — '
        f'no re-discovery, no lost context.</div></div>',
        unsafe_allow_html=True,
    )
