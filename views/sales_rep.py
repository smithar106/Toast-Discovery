"""Sales Rep experience: This Week agenda → Merchant Playbook → Submit → Handoff."""
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
    _render_known_context(merchant)

    if _is_submitted(merchant["id"]):
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
        return

    _render_context_brief(merchant, answers, evaluation)
    discovery_form.render_discovery_form(merchant, answers, evaluation)
    evaluation = evaluate_merchant(merchant, answers)
    _render_additional_context(merchant, answers, evaluation)
    _render_submission(merchant, answers, evaluation, notes_key)


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


def _render_known_context(merchant: dict) -> None:
    known = merchant.get("known", {})
    if not known:
        return
    chips = "".join(
        f'<span class="chip chip-blue" style="margin:1px 3px 1px 0;">{v.get("label", k)}: {v.get("value")}</span>'
        for k, v in known.items()
    )
    st.markdown(
        f'<div class="panel" style="margin-bottom:1rem; padding:0.7rem 1rem;">'
        f'<div class="section-title">Already known · from CRM</div>'
        f'<div style="font-size:0.8rem; margin-bottom:0.35rem;">{chips}</div>'
        f'<div class="faint small">Prepopulated from Salesforce — you will not be asked to re-enter this.</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_context_brief(merchant: dict, answers: dict, evaluation: dict) -> None:
    insight = ai_service.contextualize_merchant(merchant, answers, evaluation["critical_missing"])
    # enforce 1-2 sentences for glanceability
    sentences = [s.strip() for s in insight.split(". ") if s.strip()][:2]
    brief = ". ".join(sentences).strip()
    label = "LLM" if ai_service.ai_available() else "Auto"
    st.markdown(
        f'<div class="brief" style="margin-bottom:1rem;">'
        f'<div class="brief-title">Focus for this meeting · <span style="text-transform:none; letter-spacing:0; font-weight:500;">{label}</span></div>'
        f'<div style="font-size:0.92rem; color:{ui.INK};">{brief}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_additional_context(merchant: dict, answers: dict, evaluation: dict) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Additional context</div>', unsafe_allow_html=True)
    notes_key = f"notes_{merchant['id']}"
    st.text_area(
        "Free-text notes",
        value=st.session_state.get(notes_key, ""),
        key=notes_key,
        height=80,
        label_visibility="collapsed",
        placeholder="Merchant observations, priorities, open questions…",
    )

    st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)
    up_key = f"rec_{merchant['id']}"
    uploaded = st.file_uploader(
        "Upload recording (mp3, wav, m4a, ogg)",
        type=["mp3", "wav", "m4a", "ogg"],
        key=up_key,
        label_visibility="collapsed",
    )
    if uploaded is not None:
        st.markdown(
            f'<div class="note" style="margin-bottom:0.6rem;">Recording received: <b>{uploaded.name}</b>. '
            f'Simulated transcription + AI extraction running…</div>',
            unsafe_allow_html=True,
        )
        fact_key = f"ai_facts_{merchant['id']}"
        if fact_key not in st.session_state:
            notes = st.session_state.get(notes_key, "")
            combined = f"{notes} {uploaded.name.replace('-', ' ').replace('_', ' ')}"
            st.session_state[fact_key] = ai_service.extract_facts_from_text(combined, merchant)
        ai_facts = st.session_state.get(fact_key, [])
        if ai_facts:
            st.markdown(
                '<div class="faint small" style="margin-bottom:0.4rem;">Candidate facts — AI output is labeled '
                'and only counts once you confirm it:</div>',
                unsafe_allow_html=True,
            )
            for fact in ai_facts:
                confirmed_key = f"confirm_{fact['id']}_{merchant['id']}"
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f'<div class="panel" style="padding:0.5rem 0.75rem;"><b style="font-size:0.88rem;">{fact["label"]}</b>'
                        f'<div class="small muted">{fact["value"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    default_confirmed = bool(answers.get(fact["id"], {}).get("confirmed")) if fact["id"] in answers else False
                    ok = st.checkbox("Confirm", key=confirmed_key, value=default_confirmed)
                if ok:
                    answers[fact["id"]] = {"value": fact["value"], "source": "ai", "confirmed": True}
                elif fact["id"] in answers and answers[fact["id"]].get("source") == "ai":
                    answers[fact["id"]]["confirmed"] = False

    if ai_service.ai_available() and uploaded is not None:
        st.markdown('<div class="foot">Live LLM extraction active (OpenAI key detected).</div>', unsafe_allow_html=True)


def _render_submission(merchant: dict, answers: dict, evaluation: dict, notes_key: str) -> None:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    ready = evaluation["ready"]

    if not ready:
        n = len(evaluation["critical_missing"])
        items = "".join(
            f'<li style="margin-bottom:0.2rem;"><b>{r["label"]}</b></li>' for r in evaluation["critical_missing"]
        )
        st.markdown(
            f'<div class="panel" style="border:1px solid #F2D8D4; background:#FDF6F5; padding:0.9rem 1rem;">'
            f'<div class="section-title" style="color:{ui.RED};">Before you leave · {n} critical item{"s" if n != 1 else ""} remain</div>'
            f'<div class="small muted" style="margin-top:0.15rem;">Resolve these before finishing:</div>'
            f'<ul style="margin:0.45rem 0 0 1.1rem; color:{ui.INK};">{items}</ul>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if evaluation["important_missing"]:
            st.markdown(
                f'<div class="small muted" style="margin-top:0.5rem;">Optional, if time allows: '
                f'{", ".join(r["label"] for r in evaluation["important_missing"])}</div>',
                unsafe_allow_html=True,
            )
        st.button("Submit discovery", disabled=True, width="stretch",
                  help="Complete all critical requirements to submit.", type="primary")
    else:
        st.markdown(
            f'<div class="panel" style="border:1px solid #CFE5D8; background:#F3F9F5; padding:0.9rem 1rem;">'
            f'<div class="section-title" style="color:{ui.GREEN};">✓ Ready for handoff</div>'
            f'<div class="small muted">All critical requirements confirmed ({evaluation["critical_total"]} of '
            f'{evaluation["critical_total"]}). Submitting updates Salesforce and generates the onboarding handoff.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Submit discovery", width="stretch", type="primary"):
            st.session_state[f"submitted_{merchant['id']}"] = True
            st.rerun()
