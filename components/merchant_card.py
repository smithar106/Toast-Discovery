"""Merchant card for the 'This Week' list."""
from __future__ import annotations

import streamlit as st

from components import ui
from services import load_verticals
from services.validation import completeness_pct


def merchant_card(merchant: dict, answers: dict) -> None:
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])
    pct = completeness_pct(merchant, answers)
    submitted = bool(st.session_state.get(f"submitted_{merchant['id']}", False))
    status = merchant.get("discovery", {}).get("in_progress", True)
    locs = merchant.get("locations", 1)

    if submitted:
        badge = f'<span class="badge badge-blue">Submitted · handoff sent</span>'
    elif not status:
        badge = f'<span class="badge badge-green">Discovery complete</span>'
    elif pct == 100:
        badge = f'<span class="badge badge-green">Ready to submit</span>'
    elif pct >= 70:
        badge = f'<span class="badge badge-amber">In progress</span>'
    else:
        badge = f'<span class="badge badge-red">Needs attention</span>'

    st.markdown(
        f"""
        <div class="card" style="margin-bottom:0.75rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
                <div>
                    <div class="merchant-name">{merchant['name']}</div>
                    <div class="muted small" style="margin-top:0.15rem;">
                        {vname} · {locs} location{'s' if locs != 1 else ''} · {merchant.get('region','')} · {merchant.get('meeting_type','In-person')}
                    </div>
                </div>
                {badge}
            </div>
            <div style="display:flex; align-items:center; gap:1.4rem; margin-top:0.6rem; flex-wrap:wrap;">
                <span class="muted small"><b style="color:{ui.INK};">{merchant['meeting_date'][5:]}</b> · {merchant['meeting_time']}</span>
                <span class="muted small">{merchant.get('opportunity_value','—') and f"${merchant['opportunity_value']:,}"} opp</span>
                <span class="small" style="color:{ui.INK};">Completeness <b>{pct}%</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
