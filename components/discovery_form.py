"""Interactive discovery form with conditional requirements.

Compact single-panel design: requirements render as tight rows (label left,
widget right) inside one Critical panel and one quieter Important panel. The
panel header carries the "before you leave" count so the rep sees the minimum
sufficient discovery state at a glance.
"""
from __future__ import annotations

import streamlit as st

from components import ui
from services import load_requirements
from services.discovery_engine import grouped_requirements


def _existing(answers: dict, req_id: str) -> dict | None:
    entry = answers.get(req_id)
    return entry if isinstance(entry, dict) else None


def _widget_key(merchant_id: str, req_id: str) -> str:
    return f"ans_{merchant_id}_{req_id}"


def _label(req_id: str) -> str:
    for r in load_requirements():
        if r["id"] == req_id:
            return r["label"]
    return req_id


def _render_widget(merchant_id: str, req: dict, entry: dict | None, existing_value):
    """Render the correct compact widget; returns (value, changed)."""
    req_id = req["id"]
    key = _widget_key(merchant_id, req_id)
    itype = req.get("input_type")
    if existing_value is None and entry is not None:
        existing_value = entry.get("value")
    current = existing_value

    if itype == "yesno":
        value = st.segmented_control(
            "answer", options=["Yes", "No", "Unknown"], default=existing_value,
            key=key, help=req.get("help"), label_visibility="collapsed",
            format_func=lambda x: x if x else "—",
        )
    elif itype == "radio":
        options = req["options"]
        idx = options.index(existing_value) if existing_value in options else None
        value = st.radio("answer", options, index=idx, key=key, help=req.get("help"),
                         label_visibility="collapsed", horizontal=True)
    elif itype == "dropdown":
        options = ["— Select —"] + req["options"]
        idx = options.index(existing_value) if existing_value in options else 0
        value = st.selectbox("answer", options, index=idx, key=key, help=req.get("help"),
                             label_visibility="collapsed")
    elif itype == "multiselect":
        value = st.multiselect("answer", req["options"],
                               default=list(existing_value) if isinstance(existing_value, list) else [],
                               key=key, help=req.get("help"), label_visibility="collapsed",
                               max_selections=4, placeholder="Select…")
    elif itype == "number":
        value = st.number_input("answer", min_value=0, step=1,
                                value=None if existing_value is None else int(existing_value),
                                key=key, help=req.get("help"), label_visibility="collapsed")
    elif itype == "text":
        value = st.text_input("answer", value=str(existing_value) if existing_value else "",
                              key=key, help=req.get("help"),
                              placeholder=req.get("placeholder", ""), label_visibility="collapsed")
    elif itype == "textarea":
        value = st.text_area("answer", value=str(existing_value) if existing_value else "",
                             key=key, help=req.get("help"), label_visibility="collapsed")
    else:
        value = st.text_input("answer", value=str(existing_value) if existing_value else "",
                              key=key, label_visibility="collapsed")

    changed = False
    if itype == "yesno":
        changed = value is not None and value != current
    elif itype == "radio":
        changed = value is not None and value != current
    elif itype == "dropdown":
        changed = value not in ("— Select —", None) and value != current
    elif itype == "multiselect":
        changed = bool(value) and value != (current or [])
    elif itype == "number":
        changed = value is not None and value != current
    else:
        changed = bool(value) and value != (current or "")

    return value, changed


def _finalize(answers: dict, req_id: str, value, entry: dict | None, changed: bool) -> None:
    """Write the answer back with correct source/confirmation."""
    is_empty = value is None or value == "— Select —" or value == "" or value == [] or value == 0
    if is_empty:
        if entry is not None and entry.get("source") == "crm":
            return
        answers.pop(req_id, None)
        return

    new_source = "rep"
    if entry is not None and not changed:
        new_source = entry.get("source", "rep")
    confirmed = True
    if entry is not None and entry.get("source") == "ai" and not changed:
        confirmed = entry.get("confirmed", False)
    answers[req_id] = {"value": value, "source": new_source, "confirmed": confirmed}


def render_discovery_form(merchant: dict, answers: dict, evaluation: dict) -> dict:
    """Render compact Critical + Important panels; returns updated answers."""
    vertical = merchant["vertical"]
    merchant_id = merchant["id"]
    critical, important, _ = grouped_requirements(vertical, answers)

    n_missing = len(evaluation["critical_missing"])
    missing_labels = " · ".join(f'<span style="color:{ui.INK};">{r["label"]}</span>' for r in evaluation["critical_missing"])
    if n_missing:
        header_label = f"🔴 Before you leave · {n_missing} remaining"
        header_sub = f'<span style="font-weight:500; color:{ui.RED}; text-transform:none; letter-spacing:0; font-size:0.8rem;">{missing_labels}</span>'
    else:
        header_label = "🔴 Critical requirements · complete"
        header_sub = '<span class="chip chip-green">✓ Ready for handoff</span>'

    st.markdown(
        f'<div class="panel-flush" style="margin-bottom:1rem;">'
        f'<div class="critical-header"><span class="critical-title">{header_label}</span>{header_sub}</div>',
        unsafe_allow_html=True,
    )

    for req in critical:
        entry = _existing(answers, req["id"])
        source_chips = ""
        if entry:
            src = entry.get("source")
            if src == "crm":
                source_chips = ui.chip("CRM known", "blue")
            elif src == "ai":
                source_chips = ui.chip("AI extracted" if not entry.get("confirmed") else "AI confirmed", "accent")
            else:
                source_chips = ui.chip("Confirmed", "green")
        parent = req.get("condition", {}).get("field")
        child = f'<span class="q-help">after “{_label(parent)}”</span>' if parent else ""

        c1, c2 = st.columns([3.2, 2.4], gap="small")
        with c1:
            st.markdown(
                f'<div style="padding:0.45rem 0.25rem 0.45rem 1rem;"><span class="q-label">{req["question"]}</span>'
                f'<div style="display:flex; gap:0.3rem; margin-top:0.15rem;">{child}{source_chips}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            value, changed = _render_widget(merchant_id, req, entry, None)
            _finalize(answers, req["id"], value, entry, changed)
        if req is not critical[-1]:
            st.markdown('<div style="border-top:1px solid #EFF0F1; margin:0 1rem;"></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if important:
        st.markdown(
            f'<div class="panel-flush" style="margin-bottom:1rem;">'
            f'<div class="important-header"><span class="important-title">🟡 If time allows</span></div>',
            unsafe_allow_html=True,
        )
        for req in important:
            entry = _existing(answers, req["id"])
            source_chips = ""
            if entry:
                src = entry.get("source")
                if src == "crm":
                    source_chips = ui.chip("CRM known", "blue")
                elif src == "ai":
                    source_chips = ui.chip("AI extracted" if not entry.get("confirmed") else "AI confirmed", "accent")
                else:
                    source_chips = ui.chip("Confirmed", "green")
            parent = req.get("condition", {}).get("field")
            child = f'<span class="q-help">after “{_label(parent)}”</span>' if parent else ""

            c1, c2 = st.columns([3.2, 2.4], gap="small")
            with c1:
                st.markdown(
                    f'<div style="padding:0.42rem 0.25rem 0.42rem 1rem;"><span class="q-label" style="color:{ui.MUTED};">{req["question"]}</span>'
                    f'<div style="display:flex; gap:0.3rem; margin-top:0.15rem;">{child}{source_chips}</div></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                value, changed = _render_widget(merchant_id, req, entry, None)
                _finalize(answers, req["id"], value, entry, changed)
            if req is not important[-1]:
                st.markdown('<div style="border-top:1px solid #EFF0F1; margin:0 1rem;"></div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    return answers
