"""Interactive discovery form with conditional requirements.

Each governed requirement renders inside a collapsible dropdown (expander) so
the playbook reads as tidy sections instead of a long flat list. The expander
title carries the question + a status chip; opening it reveals the help text and
the answer widget. Confirmed answers collapse by default.

Confirmed answers render as read-only rows (with a CONFIRMED chip) rather than
live widgets — the rep is never asked to re-enter information already captured.
"""
from __future__ import annotations

import streamlit as st

from components import ui
from services import load_requirements
from services.discovery_engine import grouped_requirements


def _format_value(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value) if value not in (None, "") else "—"


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


def _source_chips(entry: dict | None) -> str:
    if not entry:
        return ""
    src = entry.get("source")
    if src == "crm":
        return ui.chip("GOVERNED · from CRM", "blue")
    if src == "ai":
        if entry.get("confirmed"):
            return ui.chip("AI ASSISTED · confirmed", "accent")
        return ui.chip("AI ASSISTED · needs confirm", "accent")
    return ui.chip("CONFIRMED", "green")


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


def _section_header(label: str, sub: str, tone: str) -> None:
    bg = {"red": "#FDF6F5", "amber": "#FAF3E3"}[tone]
    border = {"red": "#F2D8D4", "amber": "#EFE3C8"}[tone]
    color = {"red": ui.RED, "amber": ui.AMBER}[tone]
    st.markdown(
        f'<div class="panel" style="margin-bottom:0.6rem; padding:0.7rem 1rem; border-left:3px solid {color}; background:{bg};">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; flex-wrap:wrap;">'
        f'<span style="font-size:0.85rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; color:{color};">{label}</span>'
        f'<span style="font-size:0.82rem; color:{ui.INK};">{sub}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render_discovery_form(merchant: dict, answers: dict, evaluation: dict) -> dict:
    """Render Critical + Important sections as collapsible dropdowns."""
    vertical = merchant["vertical"]
    merchant_id = merchant["id"]
    critical, important, _ = grouped_requirements(vertical, answers)

    n_missing = len(evaluation["critical_missing"])

    # ---- Critical requirements section ----
    if n_missing:
        labels = ", ".join(r["label"] for r in evaluation["critical_missing"])
        _section_header(
            "🔴 Critical requirements · before you leave",
            f"{n_missing} remaining — {labels}",
            "red",
        )
    else:
        _section_header(
            "🔴 Critical requirements · complete",
            "✓ Ready for handoff — all governed requirements confirmed",
            "red",
        )

    for req in critical:
        entry = _existing(answers, req["id"])
        is_confirmed = bool(entry and entry.get("confirmed"))
        chips = _source_chips(entry)
        parent = req.get("condition", {}).get("field")
        child = f'<span class="q-help">after “{_label(parent)}”</span>' if parent else ""

        if is_confirmed:
            # collapsed read-only row
            title = f"✓ {req['question']} — {_format_value(entry.get('value'))}"
            with st.expander(title, expanded=False):
                st.markdown(
                    f'<div class="small" style="color:{ui.INK};">{child} {chips} '
                    f'<span class="faint small">{req.get("help", "")}</span></div>',
                    unsafe_allow_html=True,
                )
            continue

        title = f"{req['question']} {chips}"
        with st.expander(title, expanded=True):
            if req.get("help"):
                st.markdown(
                    f'<div class="small" style="color:{ui.INK}; margin-bottom:0.4rem;">{child} '
                    f'<span class="faint small">{req["help"]}</span></div>',
                    unsafe_allow_html=True,
                )
            value, changed = _render_widget(merchant_id, req, entry, None)
            _finalize(answers, req["id"], value, entry, changed)

    # ---- Important / conditional section ----
    if important:
        _section_header("🟡 If time allows", "Important or conditional — not required to complete", "amber")
        for req in important:
            entry = _existing(answers, req["id"])
            is_confirmed = bool(entry and entry.get("confirmed"))
            chips = _source_chips(entry)
            parent = req.get("condition", {}).get("field")
            child = f'<span class="q-help">after “{_label(parent)}”</span>' if parent else ""

            if is_confirmed:
                title = f"✓ {req['question']} — {_format_value(entry.get('value'))}"
                with st.expander(title, expanded=False):
                    st.markdown(
                        f'<div class="small" style="color:{ui.INK};">{child} {chips} '
                        f'<span class="faint small">{req.get("help", "")}</span></div>',
                        unsafe_allow_html=True,
                    )
                continue

            title = f"{req['question']} {chips}"
            with st.expander(title, expanded=False):
                if req.get("help"):
                    st.markdown(
                        f'<div class="small" style="color:{ui.INK}; margin-bottom:0.4rem;">{child} '
                        f'<span class="faint small">{req["help"]}</span></div>',
                        unsafe_allow_html=True,
                    )
                value, changed = _render_widget(merchant_id, req, entry, None)
                _finalize(answers, req["id"], value, entry, changed)

    return answers
