"""Sales Rep experience: This Week → Merchant Playbook → Submit → Handoff."""
from __future__ import annotations

import streamlit as st

from components import discovery_form, handoff as handoff_comp, merchant_card, ui
from services import ai_service, load_merchants, load_verticals
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


def render() -> None:
    ui.page_header(
        "Toast Retail Discovery · Sales",
        "This Week",
        "Know what you cannot afford to leave without knowing.",
    )
    st.markdown(
        f'<div class="muted small" style="margin-bottom:1rem;">Rep: <b style="color:{ui.INK};">Maya Chen</b> · '
        f'Northeast region · Viewing the week of Aug 24, 2026</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("rep_view") == "playbook":
        _render_playbook()
        return

    merchants = load_merchants()
    sorted_m = sorted(merchants, key=lambda m: (m["meeting_date"], m["meeting_time"]))
    for merchant in sorted_m:
        answers = _init_session(merchant)
        merchant_card.merchant_card(merchant, answers)
        col1, _ = st.columns([1, 5])
        with col1:
            if st.button("Open Discovery Playbook", key=f"open_{merchant['id']}", width="stretch"):
                st.session_state["rep_view"] = "playbook"
                st.session_state["active_merchant"] = merchant["id"]
                st.rerun()
        st.write("")


def _render_playbook() -> None:
    merchant_id = st.session_state.get("active_merchant")
    merchant = next((m for m in load_merchants() if m["id"] == merchant_id), None)
    if merchant is None:
        st.session_state["rep_view"] = "home"
        st.rerun()

    if st.button("← Back to This Week"):
        st.session_state["rep_view"] = "home"
        st.rerun()

    answers = _init_session(merchant)
    notes_key = f"notes_{merchant['id']}"
    evaluation = evaluate_merchant(merchant, answers)
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])

    _render_header(merchant, vname, evaluation)
    ui.page_header("", "Discovery Playbook", "")

    _render_known_context(merchant)

    if _is_submitted(merchant["id"]):
        st.success("**Discovery submitted** — handoff generated below.")
        summary = ai_service.generate_summary(merchant, answers, st.session_state.get(notes_key, ""))
        handoff_comp.render_handoff(merchant, answers, st.session_state.get(notes_key, ""), summary)
        st.markdown(
            """
            <div class="card" style="margin-top:1rem;">
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
        return

    _render_context_insight(merchant, answers, evaluation)
    discovery_form.render_discovery_form(merchant, answers)
    _render_additional_context(merchant, answers, evaluation)
    evaluation = evaluate_merchant(merchant, answers)
    _render_submission(merchant, answers, evaluation, notes_key)


def _render_header(merchant: dict, vname: str, evaluation: dict) -> None:
    dm = merchant.get("decision_maker") or {}
    st.markdown(
        f"""
        <div class="card" style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                <div>
                    <div class="eyebrow">Merchant discovery workspace</div>
                    <div style="font-size:1.3rem; font-weight:700; color:{ui.INK}; margin-top:0.15rem;">{merchant['name']}</div>
                    <div class="muted small" style="margin-top:0.2rem;">
                        {vname} · {merchant.get('locations',1)} location(s) · {merchant.get('region','')} · {merchant.get('stage','Discovery')} ·
                        meeting {merchant['meeting_date']} at {merchant['meeting_time']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div class="kpi-label">Discovery completeness</div>
                    <div style="font-size:1.6rem; font-weight:700; color:{ui.ACCENT};">{evaluation['completeness_pct']}%</div>
                    <div class="small muted">{evaluation['critical_complete']}/{evaluation['critical_total']} critical · {evaluation['total_scored']} total</div>
                </div>
            </div>
            <div class="pill-row">
                <span class="badge">Opportunity: ${merchant.get('opportunity_value',0):,}</span>
                <span class="badge badge-accent">Rep: {merchant.get('rep_id','').replace('_',' ').title()}</span>
                <span class="badge badge-blue">Decision maker: {dm.get('name','—')} {'✓ confirmed' if dm.get('confirmed') else '· to confirm'}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_known_context(merchant: dict) -> None:
    known = merchant.get("known", {})
    if not known:
        return
    st.markdown('<div class="section-title">Already known (from CRM)</div>', unsafe_allow_html=True)
    chips = "".join(
        f'<span class="badge badge-blue" style="margin:2px 4px 2px 0;">{v.get("label", k)}: {v.get("value")}</span>'
        for k, v in known.items()
    )
    st.markdown(
        f'<div class="card" style="margin-bottom:1rem;"><div class="small muted" style="margin-bottom:0.4rem;">'
        f'Prepopulated from Salesforce — you will not be asked to re-enter this.</div>{chips}</div>',
        unsafe_allow_html=True,
    )


def _render_context_insight(merchant: dict, answers: dict, evaluation: dict) -> None:
    insight = ai_service.contextualize_merchant(merchant, answers, evaluation["critical_missing"])
    label = "AI context · LLM" if ai_service.ai_available() else "Context · built-in"
    st.markdown(
        f'<div class="insight"><b>What matters most for this conversation</b> '
        f'<span class="source-chip">{label}</span><div style="margin-top:0.4rem;">{insight}</div></div>',
        unsafe_allow_html=True,
    )


def _render_additional_context(merchant: dict, answers: dict, evaluation: dict) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:1.05rem;">Add additional context</div>', unsafe_allow_html=True)
    notes_key = f"notes_{merchant['id']}"
    notes = st.text_area(
        "Free-text notes & merchant observations",
        value=st.session_state.get(notes_key, ""),
        key=notes_key,
        height=110,
        label_visibility="collapsed",
        placeholder="e.g. Dana emphasized compliance concerns around fuel price signage; store manager will own training.",
    )

    st.markdown('<div class="section-title" style="margin-top:0.8rem;">Upload recording (optional)</div>', unsafe_allow_html=True)
    up_key = f"rec_{merchant['id']}"
    uploaded = st.file_uploader(
        "Upload a meeting recording (mp3, wav, m4a, ogg)",
        type=["mp3", "wav", "m4a", "ogg"],
        key=up_key,
        label_visibility="collapsed",
    )
    ai_facts = []
    if uploaded is not None:
        st.markdown(
            f'<div class="note" style="margin-bottom:0.6rem;">Recording received: <b>{uploaded.name}</b>. '
            f'Simulated transcription + AI fact extraction running…</div>',
            unsafe_allow_html=True,
        )
        # Simulate extraction: first run only, deterministic from filename+notes
        fact_key = f"ai_facts_{merchant['id']}"
        if fact_key not in st.session_state:
            combined = f"{notes} {uploaded.name.replace('-', ' ').replace('_', ' ')}"
            extracted = ai_service.extract_facts_from_text(combined, merchant)
            st.session_state[fact_key] = extracted
        ai_facts = st.session_state.get(fact_key, [])
        if ai_facts:
            st.markdown(
                '<div class="muted small" style="margin-bottom:0.4rem;">Candidate facts extracted from recording — '
                'AI output is labeled and only counts once you confirm it:</div>',
                unsafe_allow_html=True,
            )
            for fact in ai_facts:
                confirmed_key = f"confirm_{fact['id']}_{merchant['id']}"
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f'<div class="req-card"><b>{fact["label"]}</b><div class="small muted">{fact["value"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    default_confirmed = bool(answers.get(fact["id"], {}).get("confirmed")) if fact["id"] in answers else False
                    ok = st.checkbox("Confirm", key=confirmed_key, value=default_confirmed)
                if ok:
                    answers[fact["id"]] = {"value": fact["value"], "source": "ai", "confirmed": True}
                elif fact["id"] in answers and answers[fact["id"]].get("source") == "ai":
                    answers[fact["id"]]["confirmed"] = False

    # expose real AI extraction when key present
    if ai_service.ai_available() and uploaded is not None:
        st.markdown(
            f'<div class="foot">Live LLM extraction active (OpenAI key detected).</div>',
            unsafe_allow_html=True,
        )


def _render_submission(merchant: dict, answers: dict, evaluation: dict, notes_key: str) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    ready = evaluation["ready"]

    if not ready:
        st.markdown(
            f'<div class="card" style="border-color:#F5C6C2; background:#FFF7F6;">'
            f'<div class="section-title" style="color:{ui.RED};">Before you leave</div>'
            f'<div class="small" style="margin-top:0.2rem;"><b>{len(evaluation["critical_missing"])} critical '
            f'requirement{"s" if len(evaluation["critical_missing"]) != 1 else ""} remain</b> — '
            f'you cannot afford to leave without knowing these:</div>'
            f'<ul style="margin:0.5rem 0 0 1.1rem; color:{ui.INK};">'
            + "".join(f'<li><b>{r["label"]}</b> <span class="muted small">(vertical: {r["vertical"]})</span></li>' for r in evaluation["critical_missing"])
            + '</ul></div>',
            unsafe_allow_html=True,
        )
        if evaluation["important_missing"]:
            st.markdown(
                f'<div class="small muted" style="margin-top:0.5rem;">Important (non-blocking) open: '
                f'{", ".join(r["label"] for r in evaluation["important_missing"])}</div>',
                unsafe_allow_html=True,
            )
        st.button("Submit Discovery", disabled=True, width="stretch",
                  help="Complete all critical requirements to submit.", type="primary")
    else:
        st.markdown(
            f'<div class="card" style="border-color:#CBE7D8; background:#F2FAF5;">'
            f'<div class="section-title" style="color:{ui.GREEN};">All critical requirements complete</div>'
            f'<div class="small muted">Discovery is ready to submit. This will update the opportunity in Salesforce '
            f'and generate the onboarding handoff.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Submit Discovery", width="stretch", type="primary"):
            st.session_state[f"submitted_{merchant['id']}"] = True
            st.rerun()
