"""Agenda row for the 'This Week' list.

Designed for glanceability in the field: time on the left, merchant + vertical
in the middle, and status / critical-count + action on the right.
"""
from __future__ import annotations

import streamlit as st

from components import ui
from services import load_verticals
from services.validation import evaluate_merchant

_MT = {"In-person": "In person", "Phone": "Phone", "Video": "Video"}


def _time_label(merchant: dict) -> str:
    t = merchant.get("meeting_time", "")
    return t.replace(" AM", "").replace(" PM", "")


def _ampm(merchant: dict) -> str:
    return "AM" if "AM" in merchant.get("meeting_time", "") else "PM"


def merchant_card(merchant: dict, answers: dict) -> None:
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])
    ev = evaluate_merchant(merchant, answers)
    submitted = bool(st.session_state.get(f"submitted_{merchant['id']}", False))
    status = merchant.get("discovery", {}).get("in_progress", True)
    locs = merchant.get("locations", 1)
    critical_remaining = len(ev["critical_missing"])

    # Status chip + primary count (critical-first, per the thesis)
    if submitted:
        status_chip = ui.chip("Submitted", "blue")
        count = '<span class="chip chip-green">✓ Ready for handoff</span>'
    elif not status:
        status_chip = ui.chip("Complete", "green")
        count = '<span class="chip chip-green">✓ Ready for handoff</span>'
    elif critical_remaining:
        status_chip = ui.chip("Needs attention", "red")
        n = critical_remaining
        count = (
            f'<span class="chip chip-red"><span class="status-dot" style="background:{ui.RED};"></span>'
            f'{n} critical item{"s" if n != 1 else ""} to confirm</span>'
        )
    else:
        status_chip = ui.chip("In progress", "amber")
        count = '<span class="chip chip-green">✓ Critical complete</span>'

    date = merchant["meeting_date"][5:]
    time = _time_label(merchant)
    ampm = _ampm(merchant)

    st.markdown(
        f"""
        <div class="panel-flush" style="margin-bottom:0.5rem;">
            <div class="row" style="padding:0.6rem 1rem;">
                <div style="min-width:120px; flex-shrink:0;">
                    <div class="agenda-time">{time}<span style="color:{ui.FAINT}; font-size:0.75rem; font-weight:500; margin-left:2px;"> {ampm}</span></div>
                    <div class="faint" style="font-size:0.72rem; margin-top:1px;">{date} · {_MT.get(merchant.get('meeting_type',''), merchant.get('meeting_type',''))}</div>
                </div>
                <div style="flex:1; min-width:0;">
                    <span class="agenda-name">{merchant['name']}</span>
                    <span class="agenda-meta"> · {vname} · {locs} location{'s' if locs != 1 else ''}</span>
                    <div class="agenda-meta">{merchant.get('region','')} · ${merchant.get('opportunity_value',0):,} opp</div>
                </div>
                <div style="display:flex; align-items:center; gap:0.6rem; flex-shrink:0;">
                    {status_chip}
                    {count}
                    <span class="agenda-arrow">›</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open playbook", key=f"open_{merchant['id']}", width="stretch"):
        st.session_state["rep_view"] = "playbook"
        st.session_state["active_merchant"] = merchant["id"]
        st.rerun()
