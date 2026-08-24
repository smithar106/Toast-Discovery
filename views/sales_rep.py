"""Sales Rep experience: This Week agenda → Prepare for Meeting → Discovery agenda → Meeting analysis → Validate.

The flow makes the AI + deterministic boundary visible:
  - Governed requirements = deterministic business logic (requirements.json).
  - CRM / prior context = structured merchant data (crm_context.json).
  - Meeting focus + extraction = LLM interpretation (ai_service, with offline fallback).
  - Confirmation + completion = deterministic validation (validation.py).
"""
from __future__ import annotations

import time

import streamlit as st

from components import discovery_form, handoff as handoff_comp, merchant_card, ui
from services import ai_service, load_crm_context, load_merchants, load_verticals
from services.validation import evaluate_merchant


def _seed_answers(merchant: dict) -> dict:
    answers = {}
    for req_id, entry in merchant.get("answers", {}).items():
        answers[req_id] = {
            "value": entry.get("value"),
            "source": entry.get("source", "rep"),
            "confirmed": entry.get("confirmed", True),
        }
    return answers


def _init_session(merchant: dict) -> dict:
    key = f"answers_{merchant['id']}"
    if key not in st.session_state:
        st.session_state[key] = _seed_answers(merchant)
    return st.session_state[key]


def _is_submitted(merchant_id: str) -> bool:
    key = f"submitted_{merchant_id}"
    return bool(st.session_state.get(key, False))


def _is_prepared(merchant_id: str) -> bool:
    return bool(st.session_state.get(f"prepared_{merchant_id}", False))


def _is_extracted(merchant_id: str) -> bool:
    return bool(st.session_state.get(f"extracted_{merchant_id}", False))


def render() -> None:
    ui.page_header(
        "Sales · This week",
        "Discovery agenda",
    )
    st.markdown(
        f'<div class="muted small" style="margin-bottom:0.9rem;">Rep: <b style="color:{ui.INK};">Maya Chen</b> · '
        f'Northeast · week of Aug 24, 2026</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("rep_view") == "playbook":
        _render_playbook()
        return

    merchants = load_merchants()
    sorted_m = sorted(merchants, key=lambda m: (m["meeting_date"], m["meeting_time"]))
    st.markdown('<div class="section-title">Upcoming meetings</div>', unsafe_allow_html=True)
    for merchant in sorted_m:
        answers = _init_session(merchant)
        merchant_card.merchant_card(merchant, answers)


def _render_playbook() -> None:
    merchant_id = st.session_state.get("active_merchant")
    merchant = next((m for m in load_merchants() if m["id"] == merchant_id), None)
    if merchant is None:
        st.session_state["rep_view"] = "home"
        st.rerun()

    if st.button("← Back to agenda"):
        st.session_state["rep_view"] = "home"
        st.rerun()

    answers = _init_session(merchant)
    notes_key = f"notes_{merchant['id']}"
    evaluation = evaluate_merchant(merchant, answers)
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])

    _render_header(merchant, vname, evaluation)

    if _is_submitted(merchant["id"]):
        _render_submitted(merchant, answers, notes_key)
        return

    if not _is_prepared(merchant["id"]):
        _render_prepare_gate(merchant)
        return

    # Prepared → discovery agenda + post-meeting workflow
    _render_agenda(merchant, answers, evaluation, vname)
    _render_meeting_context(merchant, answers, notes_key, evaluation)


def _render_bottom_back() -> None:
    st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to agenda", width="stretch"):
        st.session_state["rep_view"] = "home"
        st.rerun()


def _render_header(merchant: dict, vname: str, evaluation: dict) -> None:
    dm = merchant.get("decision_maker") or {}
    n_missing = len(evaluation["critical_missing"])
    n_crit = evaluation["critical_total"]

    if n_missing:
        primary = f'{n_missing} critical requirement{"s" if n_missing != 1 else ""} remaining'
        sub = f'{evaluation["critical_complete"]} of {n_crit} critical confirmed'
        primary_color = ui.RED
    else:
        primary = "✓ Ready for handoff"
        sub = f'{n_crit} of {n_crit} critical confirmed'
        primary_color = ui.GREEN

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:1rem; padding:1rem 1.15rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1.5rem; flex-wrap:wrap;">
                <div>
                    <div class="eyebrow">Discovery playbook · {merchant['meeting_date']} at {merchant['meeting_time']}</div>
                    <div style="font-size:1.35rem; font-weight:700; letter-spacing:-0.02em; color:{ui.INK}; margin-top:0.1rem;">{merchant['name']}</div>
                    <div class="muted small" style="margin-top:0.15rem;">
                        {vname} · {merchant.get('locations',1)} location(s) · {merchant.get('region','')} · {merchant.get('stage','Discovery')} · ${merchant.get('opportunity_value',0):,}
                    </div>
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    <div style="font-size:1.15rem; font-weight:700; color:{primary_color};">{primary}</div>
                    <div class="small muted">{sub}</div>
                </div>
            </div>
            <div class="pill-row" style="margin-top:0.6rem;">
                <span class="chip chip-neutral">Decision maker: {dm.get('name','—')} {'✓' if dm.get('confirmed') else '· to confirm'}</span>
                <span class="chip chip-neutral">Rep: Maya Chen</span>
                <span class="chip chip-neutral">{merchant.get('meeting_type','In-person')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PREPARE GATE
# ---------------------------------------------------------------------------

def _render_prepare_gate(merchant: dict) -> None:
    st.markdown(
        f"""
        <div class="panel" style="padding:1.2rem 1.3rem; text-align:center; margin:1rem 0;">
            <div style="font-size:1.05rem; font-weight:650; color:{ui.INK};">Ready to prepare for this meeting?</div>
            <div class="muted small" style="margin:0.4rem auto 0.9rem auto; max-width:480px;">
                We'll pull together what Toast already knows about this merchant, what remains unresolved,
                and where to focus the conversation today.
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Prepare for Meeting", width="stretch", type="primary"):
        with st.spinner("Preparing your discovery agenda…"):
            time.sleep(1.4)
        st.session_state[f"prepared_{merchant['id']}"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    _render_bottom_back()


# ---------------------------------------------------------------------------
# DISCOVERY AGENDA (pre-meeting)
# ---------------------------------------------------------------------------

def _render_agenda(merchant: dict, answers: dict, evaluation: dict, vname: str) -> None:
    st.markdown(
        f'<div class="section-title" style="font-size:0.9rem;">Your discovery agenda</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="muted small" style="margin-bottom:0.7rem;">{merchant["name"]} · {merchant["meeting_date"]} at '
        f'{merchant["meeting_time"]} · Rep: Maya Chen</div>',
        unsafe_allow_html=True,
    )

    _render_what_we_know(merchant)
    _render_focus(merchant, answers, evaluation)
    _render_governed(merchant, answers, evaluation)
    _render_how_it_works()


def _status_chip(status: str) -> str:
    kinds = {
        "confirmed": "green",
        "extracted": "accent",
        "needs_confirmation": "amber",
        "unknown": "neutral",
    }
    labels = {
        "confirmed": "CONFIRMED",
        "extracted": "EXTRACTED",
        "needs_confirmation": "NEEDS CONFIRMATION",
        "unknown": "UNKNOWN",
    }
    return f'<span class="chip chip-{kinds.get(status, "neutral")}" style="font-size:0.66rem;">{labels.get(status, status.upper())}</span>'


def _render_what_we_know(merchant: dict) -> None:
    ctx = load_crm_context().get(merchant["id"])
    if not ctx:
        return
    st.markdown(
        '<div class="section-title" style="margin-top:0.9rem;">What we already know</div>',
        unsafe_allow_html=True,
    )
    rows = ""
    for fact in ctx["facts"]:
        rows += (
            f'<div class="row" style="padding:0.45rem 1rem;">'
            f'<span style="flex:1; min-width:0;"><b style="font-size:0.9rem;">{fact["label"]}:</b> '
            f'<span style="font-size:0.9rem; color:{ui.INK};">{fact["value"]}</span></span>'
            f'<span style="flex-shrink:0;">{_status_chip(fact["status"])} '
            f'<span class="faint small" style="margin-left:0.4rem;">{fact["provenance"]}</span></span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="panel-flush" style="margin-bottom:1rem;">{rows}</div>',
        unsafe_allow_html=True,
    )


def _render_focus(merchant: dict, answers: dict, evaluation: dict) -> None:
    focus = ai_service.meeting_focus(merchant, answers, evaluation["critical_missing"])
    st.markdown(
        '<div class="section-title" style="margin-top:0.9rem;">Focus for this meeting</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted small" style="margin-bottom:0.5rem;">Based on what Toast already knows and what remains '
        'unresolved, here are the areas worth focusing on today.</div>',
        unsafe_allow_html=True,
    )

    # Meeting objective
    st.markdown(
        f'<div class="panel" style="margin-bottom:0.5rem; padding:0.7rem 1rem;">'
        f'<div class="faint small" style="font-size:0.7rem; letter-spacing:0.07em; text-transform:uppercase; font-weight:600;">Meeting objective</div>'
        f'<div style="font-size:0.93rem; color:{ui.INK}; margin-top:0.15rem;">{focus["objective"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for pri in focus["priorities"]:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:0.5rem; padding:0.75rem 1rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:650; color:{ui.RED}; font-size:0.95rem;">🔴 {pri['requirement']}</span>
                    <span class="chip chip-accent">AI ASSISTED</span>
                </div>
                <div class="small" style="margin-top:0.4rem;"><b>What we already know:</b> {pri['what_we_know']}</div>
                <div class="small" style="margin-top:0.2rem;"><b>Priority for this conversation:</b> {pri['requirement']}</div>
                <div class="small" style="margin-top:0.2rem;"><b>Suggested approach:</b> {pri['suggested_approach']}</div>
                <div class="small muted" style="margin-top:0.2rem;"><b>Why this matters:</b> {pri['why_it_matters']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if not focus["priorities"]:
        st.markdown(
            '<div class="small muted" style="margin-bottom:0.6rem;">All critical requirements are confirmed. '
            'Use the meeting for important context and timeline confirmation.</div>',
            unsafe_allow_html=True,
        )


def _render_governed(merchant: dict, answers: dict, evaluation: dict) -> None:
    st.markdown(
        '<div class="section-title" style="margin-top:0.9rem;">Governed requirements</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted small" style="margin-bottom:0.5rem;">Toast-defined requirements for this merchant type. '
        'These determine whether discovery is complete.</div>',
        unsafe_allow_html=True,
    )
    discovery_form.render_discovery_form(merchant, answers, evaluation)


def _render_how_it_works() -> None:
    with st.expander("How this works"):
        st.markdown(
            """
            <div class="small" style="line-height:1.9;">
            1. <b>Toast defines required discovery information.</b> <span class="chip chip-neutral">DETERMINISTIC</span><br>
            2. <b>AI interprets CRM notes and merchant context.</b> <span class="chip chip-accent">LLM</span><br>
            3. <b>AI prepares merchant-specific meeting guidance.</b> <span class="chip chip-accent">LLM</span><br>
            4. <b>Rep conducts discovery.</b> <span class="chip chip-blue">HUMAN</span><br>
            5. <b>AI extracts candidate answers from notes / recording.</b> <span class="chip chip-accent">LLM</span><br>
            6. <b>Rep confirms extracted information.</b> <span class="chip chip-blue">HUMAN</span><br>
            7. <b>System validates required fields.</b> <span class="chip chip-neutral">DETERMINISTIC</span><br>
            8. <b>Complete handoff moves to onboarding.</b> <span class="chip chip-neutral">DETERMINISTIC</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# POST-MEETING: context → extract → confirm → validate
# ---------------------------------------------------------------------------

def _render_meeting_context(merchant: dict, answers: dict, notes_key: str, evaluation: dict) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Add meeting context</div>', unsafe_allow_html=True)
    st.text_area(
        "Free-text notes",
        value=st.session_state.get(notes_key, ""),
        key=notes_key,
        height=80,
        label_visibility="collapsed",
        placeholder="Merchant observations, priorities, answers given during the meeting…",
    )
    st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)
    up_key = f"rec_{merchant['id']}"
    uploaded = st.file_uploader(
        "Upload recording (mp3, wav, m4a, ogg)",
        type=["mp3", "wav", "m4a", "ogg"],
        key=up_key,
        label_visibility="collapsed",
    )
    has_context = bool(st.session_state.get(notes_key, "").strip()) or uploaded is not None
    if not _is_extracted(merchant["id"]):
        if st.button(
            "Summarize & Extract", width="stretch", type="primary", disabled=not has_context,
            help="Add notes or a recording first.",
        ):
            with st.spinner("Interpreting the meeting against governed requirements…"):
                time.sleep(1.6)
            st.session_state[f"extracted_{merchant['id']}"] = True
            st.rerun()
    else:
        _render_meeting_analysis(merchant, answers, notes_key, evaluation)


def _render_meeting_analysis(merchant: dict, answers: dict, notes_key: str, evaluation: dict) -> None:
    analysis = ai_service.meeting_analysis(merchant["id"]) or {"extractions": [], "gaps": []}

    st.markdown(
        '<div class="section-title" style="margin-top:1rem;">Outstanding items before submission</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="muted small" style="margin-bottom:0.5rem;">"I found evidence related to the following discovery '
        'requirements. Review the extracted information before saving."</div>',
        unsafe_allow_html=True,
    )

    if analysis.get("summary"):
        st.markdown(
            f'<div class="panel" style="margin-bottom:0.6rem; padding:0.7rem 1rem;">'
            f'<div class="faint small" style="font-size:0.7rem; letter-spacing:0.07em; text-transform:uppercase; font-weight:600;">Meeting summary</div>'
            f'<div style="font-size:0.9rem; color:{ui.INK}; margin-top:0.15rem;">{analysis["summary"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if analysis["extractions"]:
        for item in analysis["extractions"]:
            _render_extraction_item(merchant, answers, item)
    else:
        st.markdown(
            '<div class="small muted" style="margin-bottom:0.6rem;">No candidate facts were extracted from the '
            'provided context.</div>',
            unsafe_allow_html=True,
        )

    # Confirm-all shortcut when extractions exist but some are unconfirmed
    pending = [i for i in analysis["extractions"] if not (answers.get(i["req_id"]) or {}).get("confirmed")]
    if pending:
        if st.button("Confirm all extracted answers", width="stretch", type="primary",
                     key=f"confirm_all_{merchant['id']}"):
            for item in analysis["extractions"]:
                answers[item["req_id"]] = {
                    "value": item["suggested_value"],
                    "source": "ai",
                    "confirmed": True,
                }

    # Deterministic validation after confirmation
    evaluation = evaluate_merchant(merchant, answers)
    if evaluation["ready"]:
        _render_complete(merchant, answers, notes_key)
    else:
        _render_gaps(merchant, answers, evaluation)


def _render_extraction_item(merchant: dict, answers: dict, item: dict) -> None:
    req_id = item["req_id"]
    store_key = f"extract_value_{merchant['id']}_{req_id}"
    editing_key = f"editing_{merchant['id']}_{req_id}"
    confirmed = bool(answers.get(req_id, {}).get("confirmed")) if answers.get(req_id) else False

    suggested = item["suggested_value"]
    evidence = item["evidence"]
    source_note = item.get("source_note", "Meeting context")

    if confirmed:
        saved_value = answers[req_id]["value"]
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:0.5rem; padding:0.7rem 1rem; border-color:#CFE5D8;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:650; color:{ui.INK}; font-size:0.95rem;">{item['label']}</span>
                    <span class="chip chip-green">CONFIRMED</span>
                </div>
                <div class="small" style="margin-top:0.35rem;"><b>Saved value:</b> {saved_value}</div>
                <div class="small muted">Evidence: {evidence}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom:0.5rem; padding:0.7rem 1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:650; color:{ui.INK}; font-size:0.95rem;">{item['label']}</span>
                <span class="chip chip-accent">AI EXTRACTED</span>
            </div>
            <div class="small" style="margin-top:0.35rem;"><b>Suggested value:</b> {suggested}</div>
            <div class="small muted" style="margin-top:0.15rem;">Evidence: {evidence} · <span class="faint">{source_note}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("Confirm", key=f"confirm_extract_{merchant['id']}_{req_id}", width="stretch"):
            answers[req_id] = {"value": suggested, "source": "ai", "confirmed": True}
    with c2:
        if st.button("Edit", key=f"edit_extract_{merchant['id']}_{req_id}", width="stretch"):
            st.session_state[editing_key] = True
            st.session_state[store_key] = suggested
            st.rerun()

    if st.session_state.get(editing_key):
        edited = st.text_input("Edit value", value=st.session_state.get(store_key, suggested),
                               key=f"edit_input_{merchant['id']}_{req_id}", label_visibility="collapsed")
        if st.button("Save edited value", key=f"save_edit_{merchant['id']}_{req_id}"):
            answers[req_id] = {"value": edited.strip(), "source": "ai", "confirmed": True}
            st.session_state[editing_key] = False


def _render_complete(merchant: dict, answers: dict, notes_key: str) -> None:
    evaluation = evaluate_merchant(merchant, answers)
    st.markdown(
        f"""
        <div class="panel" style="border:1px solid #CFE5D8; background:#F3F9F5; margin-top:1rem; padding:1rem 1.1rem;">
            <div class="section-title" style="color:{ui.GREEN};">Discovery complete</div>
            <div class="small" style="color:{ui.INK}; margin-top:0.2rem;">
                {evaluation['critical_total']} of {evaluation['critical_total']} critical requirements confirmed.
                The information required for onboarding is complete.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Save & Send to Onboarding", width="stretch", type="primary"):
        st.session_state[f"submitted_{merchant['id']}"] = True
        st.rerun()
    _render_bottom_back()


def _render_gaps(merchant: dict, answers: dict, evaluation: dict) -> None:
    st.markdown(
        f"""
        <div class="panel" style="border:1px solid #F2D8D4; background:#FDF6F5; margin-top:1rem; padding:1rem 1.1rem;">
            <div class="section-title" style="color:{ui.RED};">Discovery gaps remain</div>
            <div class="small muted" style="margin-top:0.2rem;">
                The meeting provided evidence for {evaluation['critical_total'] - len(evaluation['critical_missing'])} of
                {evaluation['critical_total']} required items.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # gaps: critical still missing (with extraction reasons where available)
    analysis = ai_service.meeting_analysis(merchant["id"]) or {}
    gap_reasons = {g["req_id"]: g["reason"] for g in analysis.get("gaps", [])}
    for r in evaluation["critical_missing"]:
        reason = gap_reasons.get(r["id"], "No sufficient evidence found in the meeting.")
        st.markdown(
            f'<div class="panel" style="margin-top:0.5rem; padding:0.65rem 1rem;">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<span style="font-weight:600; color:{ui.INK}; font-size:0.92rem;">🔴 {r["label"]}</span></div>'
            f'<div class="small muted" style="margin-top:0.25rem;">{reason}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="small" style="margin-top:0.7rem; color:{ui.INK};">Suggested next step: follow up with the merchant '
        f'before submitting the onboarding handoff.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 2], gap="small")
    with c1:
        if st.button("Draft Follow-Up", width="stretch"):
            gaps = [{"label": r["label"], "reason": gap_reasons.get(r["id"], "")} for r in evaluation["critical_missing"]]
            draft = ai_service.draft_follow_up(merchant, gaps)
            st.session_state[f"followup_{merchant['id']}"] = draft
            st.rerun()
    with c2:
        st.button("Send to Onboarding", width="stretch", disabled=True,
                  help="All critical requirements must be confirmed first.")

    if st.session_state.get(f"followup_{merchant['id']}"):
        with st.expander("Follow-up draft"):
            st.code(st.session_state[f"followup_{merchant['id']}"], language="markdown")
    _render_bottom_back()


# ---------------------------------------------------------------------------
# SUBMITTED
# ---------------------------------------------------------------------------

def _render_submitted(merchant: dict, answers: dict, notes_key: str) -> None:
    st.success("**Discovery submitted** — handoff generated below.")
    summary = ai_service.generate_summary(merchant, answers, st.session_state.get(notes_key, ""))
    handoff_comp.render_handoff(merchant, answers, st.session_state.get(notes_key, ""), summary)
    st.markdown(
        """
        <div class="panel" style="margin-top:1rem;">
            <div class="section-title">Submission confirmations</div>
            <div class="small" style="line-height:1.9;">
            ✅ Salesforce opportunity updated<br>
            ✅ Structured discovery record saved<br>
            ✅ Onboarding handoff generated<br>
            ✅ Onboarding Consultant notified
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_bottom_back()
