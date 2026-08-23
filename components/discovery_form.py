"""Interactive discovery form with conditional requirements.

Answers are stored per-merchant in st.session_state and keyed by requirement id.
Rendering order follows the requirements library; conditions are re-evaluated
on every rerun so child questions appear as soon as their parent is answered.
"""
from __future__ import annotations

import streamlit as st

from components import ui
from services.discovery_engine import grouped_requirements


def _existing(answers: dict, req_id: str) -> dict | None:
    entry = answers.get(req_id)
    return entry if isinstance(entry, dict) else None


def _widget_key(merchant_id: str, req_id: str) -> str:
    return f"ans_{merchant_id}_{req_id}"


def _render_widget(merchant_id: str, req: dict, entry: dict | None, default_value=None):
    """Render the correct widget; returns (value, changed)."""
    req_id = req["id"]
    key = _widget_key(merchant_id, req_id)
    itype = req.get("input_type")
    existing_value = default_value if default_value is not None else (entry.get("value") if entry else None)
    current = existing_value

    if itype == "yesno":
        options = ["Yes", "No", "Unknown"]
        value = st.segmented_control(
            req["question"], options=options, default=existing_value,
            key=key, help=req.get("help"), label_visibility="collapsed",
        )
        current = existing_value
    elif itype == "radio":
        options = req["options"]
        idx = None
        if existing_value in options:
            idx = options.index(existing_value)
        value = st.radio(req["question"], options, index=idx,
                         key=key, help=req.get("help"), horizontal=True)
        current = existing_value
    elif itype == "dropdown":
        options = ["— Select —"] + req["options"]
        idx = 0
        if existing_value in options:
            idx = options.index(existing_value)
        value = st.selectbox(req["question"], options, index=idx, key=key,
                             help=req.get("help"), label_visibility="collapsed")
        current = existing_value
    elif itype == "multiselect":
        value = st.multiselect(req["question"], req["options"],
                               default=list(existing_value) if isinstance(existing_value, list) else [],
                               key=key, help=req.get("help"), label_visibility="collapsed")
        current = existing_value
    elif itype == "number":
        value = st.number_input(req["question"], min_value=0, step=1,
                                value=None if existing_value is None else int(existing_value),
                                key=key, help=req.get("help"), label_visibility="collapsed")
        current = existing_value
    elif itype == "text":
        value = st.text_input(req["question"], value=str(existing_value) if existing_value else "",
                              key=key, help=req.get("help"),
                              placeholder=req.get("placeholder", ""), label_visibility="collapsed")
        current = existing_value
    elif itype == "textarea":
        value = st.text_area(req["question"], value=str(existing_value) if existing_value else "",
                             key=key, help=req.get("help"), label_visibility="collapsed")
        current = existing_value
    else:
        value = st.text_input(req["question"], value=str(existing_value) if existing_value else "",
                              key=key, label_visibility="collapsed")
        current = existing_value

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


def render_discovery_form(merchant: dict, answers: dict) -> dict:
    """Render critical + important sections; returns updated answers dict."""
    vertical = merchant["vertical"]
    merchant_id = merchant["id"]
    critical, important, _ = grouped_requirements(vertical, answers)

    st.markdown('<div class="section-title" style="font-size:1.05rem;">🔴 Critical requirements</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted small" style="margin-bottom:0.6rem;">Information that can determine '
        'viability, implementation design, or cause downstream rework if missed.</div>',
        unsafe_allow_html=True)

    for req in critical:
        entry = _existing(answers, req["id"])
        parent = req.get("condition", {}).get("field")
        child_of = f'<span class="muted small" style="margin-left:6px;">after “{_label(parent)}”</span>' if parent else ""
        source = ""
        if entry:
            src = entry.get("source")
            src_cls = "badge badge-blue" if src == "crm" else ("badge badge-accent" if src == "ai" else "badge badge-green")
            src_lbl = {"crm": "Known · CRM", "ai": "AI extracted", "rep": "Rep confirmed"}[src]
            source = f'<span class="{src_cls}" style="margin-left:6px;">{src_lbl}</span>'
            if src == "ai" and not entry.get("confirmed"):
                source += '<span class="badge badge-amber" style="margin-left:4px;">needs confirmation</span>'

        st.markdown(
            f"""
            <div class="req-card">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
                    <div>
                        <span class="req-question">{req['question']}</span>{child_of}
                    </div>
                    <div style="display:flex; gap:4px; flex-shrink:0;">{source}</div>
                </div>
                <div style="margin-top:0.5rem;">
            """,
            unsafe_allow_html=True,
        )
        value, changed = _render_widget(merchant_id, req, entry, None)
        _finalize(answers, req["id"], value, entry, changed)
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:1.05rem;">🟡 Important / conditional</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="muted small" style="margin-bottom:0.6rem;">Matters depending on merchant context. '
        'Not required to mark discovery complete.</div>',
        unsafe_allow_html=True)

    for req in important:
        entry = _existing(answers, req["id"])
        parent = req.get("condition", {}).get("field")
        child_of = f'<span class="muted small" style="margin-left:6px;">after “{_label(parent)}”</span>' if parent else ""
        source = ""
        if entry:
            src = entry.get("source")
            src_cls = "badge badge-blue" if src == "crm" else ("badge badge-accent" if src == "ai" else "badge badge-green")
            src_lbl = {"crm": "Known · CRM", "ai": "AI extracted", "rep": "Rep confirmed"}[src]
            source = f'<span class="{src_cls}" style="margin-left:6px;">{src_lbl}</span>'
        st.markdown(
            f"""
            <div class="req-card">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
                    <div><span class="req-question">{req['question']}</span>{child_of}</div>
                    <div style="display:flex; gap:4px; flex-shrink:0;">{source}</div>
                </div>
                <div style="margin-top:0.5rem;">
            """,
            unsafe_allow_html=True,
        )
        value, changed = _render_widget(merchant_id, req, entry, None)
        _finalize(answers, req["id"], value, entry, changed)
        st.markdown("</div></div>", unsafe_allow_html=True)

    return answers


def _label(req_id: str) -> str:
    from services import load_requirements
    for r in load_requirements():
        if r["id"] == req_id:
            return r["label"]
    return req_id
