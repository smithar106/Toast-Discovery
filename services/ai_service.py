"""Optional AI service.

LLM is used only for interpretation and contextualization. The demo must work
without any API key: every function falls back to deterministic, rule-based
behavior that still produces useful output. AI-derived facts are always labeled
and never silently satisfy critical requirements (see validation._is_confirmed).
"""
from __future__ import annotations

import json
import os

from services import load_verticals

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("TOAST_OPENAI_MODEL", "gpt-4o-mini")


def ai_available() -> bool:
    return bool(OPENAI_KEY)


def _chat(messages: list[dict]) -> str | None:
    if not OPENAI_KEY:
        return None
    try:
        import openai

        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
        return resp.choices[0].message.content
    except Exception:
        return None


def contextualize_merchant(merchant: dict, answers: dict, critical_missing: list[dict]) -> str:
    """Produce a short 'what matters most for this conversation' summary."""
    vertical = merchant["vertical"]
    vname = load_verticals().get(vertical, {}).get("name", vertical)
    known = merchant.get("known", {})
    locs = merchant.get("locations", 1)
    notes = merchant.get("notes", "")

    if not OPENAI_KEY:
        return _fallback_context(merchant, answers, critical_missing, vname, known, locs, notes)

    req_text = ", ".join(r["label"] for r in critical_missing) if critical_missing else "none"
    known_text = "; ".join(f"{k}: {v.get('value')}" for k, v in known.items()) if known else "none"
    prompt = (
        f"Merchant: {merchant['name']} ({vname}, {locs} locations). "
        f"Known: {known_text}. Open critical gaps: {req_text}. Rep notes: {notes}. "
        "Write 2-3 concise sentences on what matters most for this merchant's discovery conversation. "
        "Be specific to retail/restaurant tech. No markdown."
    )
    out = _chat([{"role": "user", "content": prompt}])
    return out.strip() if out else _fallback_context(merchant, answers, critical_missing, vname, known, locs, notes)


def _fallback_context(merchant, answers, critical_missing, vname, known, locs, notes) -> str:
    lines = []
    if critical_missing:
        labels = [r["label"] for r in critical_missing]
        if len(labels) == 1:
            lines.append(f"Confirm {labels[0].lower()} before you leave — it shapes configuration and can't be added cleanly after sign-off.")
        else:
            lines.append(f"Confirm {' and '.join(l.lower() for l in labels)} before you leave — they shape configuration and drive rework if missed.")
    else:
        lines.append("All critical requirements are confirmed. Use remaining time on important context and the target timeline.")
    if locs and int(locs) > 1:
        lines.append("Multi-location rollout — confirm whether configuration should be centralized or store-by-store.")
    return " ".join(lines)


def extract_facts_from_text(text: str, merchant: dict) -> list[dict]:
    """Extract candidate facts from notes/transcription.

    Demo fallback uses lightweight keyword matching. Real implementation would
    call the LLM, but the output shape (id, label, value, source='ai',
    confirmed=False) stays identical.
    """
    if not OPENAI_KEY:
        return _fallback_extract(text, merchant)
    prompt = (
        f"From the following merchant discovery notes, extract up to 4 discrete factual claims as JSON "
        f"list of {{'id': slug, 'label': short label, 'value': the fact}}. Only include facts not obviously "
        f"already known. Notes: {text}"
    )
    out = _chat([{"role": "user", "content": prompt}])
    if out:
        try:
            start = out.find("[")
            end = out.rfind("]") + 1
            data = json.loads(out[start:end])
            return [
                {"id": f"ai_{d.get('id','fact')}", "label": d.get("label", "Extracted fact"),
                 "value": d.get("value", ""), "source": "ai", "confirmed": False}
                for d in data[:4]
            ]
        except Exception:
            pass
    return _fallback_extract(text, merchant)


def _fallback_extract(text: str, merchant: dict) -> list[dict]:
    text_l = text.lower()
    candidates = []
    rules = [
        ("has_warehouse", "Warehouse / storage", ["warehouse", "storage", "back room"]),
        ("owns_fleet", "Fleet / delivery vehicles", ["fleet", "delivery van", "truck"]),
        ("open_weekends", "Weekend / extended hours", ["24/7", "open 24", "overnight"]),
        ("staff_count", "Staff count mentioned", ["employees", "staff", "people work"]),
        ("second_location", "Second location planned", ["second location", "new location", "expand"]),
    ]
    for fact_id, label, keywords in rules:
        if any(k in text_l for k in keywords):
            snippet = next((s.strip() for s in text.split(".") if any(k in s.lower() for k in keywords)), "")
            candidates.append({"id": fact_id, "label": label, "value": snippet, "source": "ai", "confirmed": False})
    return candidates[:4]


def generate_summary(merchant: dict, answers: dict, notes: str) -> str:
    """Short narrative summary for the onboarding handoff."""
    if not OPENAI_KEY:
        return _fallback_summary(merchant, answers, notes)
    known_text = "; ".join(f"{k}: {v.get('value')}" for k, v in (merchant.get("known") or {}).items())
    answered = "; ".join(f"{k}: {answers.get(k, {}).get('value') if isinstance(answers.get(k), dict) else answers.get(k)}" for k in answers)
    prompt = (
        f"Write a 3-4 sentence merchant discovery summary for an onboarding handoff. "
        f"Merchant: {merchant['name']}. Known context: {known_text}. Confirmed discovery: {answered}. "
        f"Rep notes: {notes}. Professional, no markdown."
    )
    out = _chat([{"role": "user", "content": prompt}])
    return out.strip() if out else _fallback_summary(merchant, answers, notes)


def _fallback_summary(merchant, answers, notes) -> str:
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])
    parts = [
        f"{merchant['name']} is a {vname.lower()} merchant with {merchant.get('locations', 1)} location(s) in the {merchant.get('region', '')} region."
    ]
    confirmed = [(k, v) for k, v in (answers or {}).items()
                 if isinstance(v, dict) and v.get("value") not in (None, "", [], "Unknown")]
    if confirmed:
        parts.append(f"Discovery confirmed {len(confirmed)} key operational requirements across POS, integrations, and hardware.")
    if notes:
        parts.append(f"Rep noted: {notes[:120]}...")
    else:
        parts.append("Rep captured additional merchant context during the meeting.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Revenue Optimization Plan — AI enhancement (with deterministic fallback)
# ---------------------------------------------------------------------------

_CATEGORY_SUMMARY = {
    "prevent": "Improve discovery itself so the requirement is surfaced during the meeting.",
    "predict": "Use merchant context and CRM data to flag the requirement earlier.",
    "protect": "Add a validation or workflow safeguard before handoff.",
}


def explain_friction(driver: dict) -> str:
    """Human explanation of a friction driver. LLM may enhance; fallback is deterministic."""
    if not OPENAI_KEY:
        return driver["explanation"]
    prompt = (
        f"Rewrite in 2 sentences why '{driver['requirement']}' for {driver['vertical_label']} merchants "
        f"creates discovery friction and downstream rework. Base context: {driver['explanation']}. "
        f"Do not mention dollar figures. Plain text, no markdown."
    )
    out = _chat([{"role": "user", "content": prompt}])
    return out.strip() if out else driver["explanation"]


def explain_option(driver: dict, option: dict) -> str:
    """Short 'why this approach' note for an option card. Fallback is category-driven."""
    if not OPENAI_KEY:
        return _CATEGORY_SUMMARY.get(option["category"], option["name"])
    prompt = (
        f"In one sentence, explain why '{option['name']}' (category: {option['category']}) is a credible "
        f"intervention for reducing '{driver['requirement']}' friction in {driver['vertical_label']} discovery. "
        f"Plain text, no markdown, no numbers."
    )
    out = _chat([{"role": "user", "content": prompt}])
    return out.strip() if out else _CATEGORY_SUMMARY.get(option["category"], option["name"])


def draft_plan_narrative(driver: dict, option: dict, plan: dict) -> str:
    """Optional narrative framing for the project plan. Fallback returns an empty string
    (the deterministic markdown plan stands on its own)."""
    if not OPENAI_KEY:
        return ""
    prompt = (
        f"Write a 2-3 sentence executive summary of a project plan to reduce '{driver['requirement']}' "
        f"friction via '{option['name']}'. Constraint: do not compute or state any dollar figures. Plain text."
    )
    out = _chat([{"role": "user", "content": prompt}])
    return out.strip() if out else ""


# ---------------------------------------------------------------------------
# Sales Rep — meeting focus, analysis, follow-up (AI with deterministic fallback)
# ---------------------------------------------------------------------------

def _requirement_meta(req_id: str) -> dict:
    from services import load_requirements
    for r in load_requirements():
        if r["id"] == req_id:
            return r
    return {"id": req_id, "label": req_id, "rule": "", "question": ""}


def meeting_focus(merchant: dict, answers: dict, critical_missing: list[dict]) -> list[dict]:
    """Build 1-3 contextual priorities for this merchant's meeting.

    The governed requirement is deterministic; what we know, the suggested
    approach, and why it matters are the LLM contextualizing it for THIS merchant.
    Deterministic fallback is used when no API key is present.
    """
    priorities = []
    for req in critical_missing[:3]:
        meta = _requirement_meta(req["id"])
        priorities.append({
            "req_id": req["id"],
            "requirement": meta.get("label", req["id"]),
            "what_we_know": _focus_what_we_know(merchant, req["id"]),
            "suggested_approach": _focus_approach(meta, merchant),
            "why_it_matters": meta.get("rule", "Required for a complete sales-to-onboarding handoff."),
        })

    if OPENAI_KEY and priorities:
        req_text = "; ".join(p["requirement"] for p in priorities)
        known_text = "; ".join(f"{k}: {v.get('value')}" for k, v in merchant.get("known", {}).items())
        prompt = (
            f"For merchant {merchant['name']} ({merchant['vertical']}), produce a JSON list of up to 3 priorities "
            f"for a discovery meeting, one per unresolved requirement: {req_text}. Known context: {known_text}. "
            f"Each item: {{'requirement','what_we_know','suggested_approach','why_it_matters'}}. "
            f"Suggested approaches are direct questions the rep can ask the merchant. Plain JSON array only."
        )
        out = _chat([{"role": "user", "content": prompt}])
        if out:
            try:
                start, end = out.find("["), out.rfind("]") + 1
                data = json.loads(out[start:end])
                if isinstance(data, list) and data:
                    return data[:3]
            except Exception:
                pass
    return priorities


def _focus_what_we_know(merchant: dict, req_id: str) -> str:
    known = merchant.get("known", {})
    if req_id == "decision_maker":
        dm = merchant.get("decision_maker") or {}
        if dm.get("name"):
            return (f"{dm['name']} is the primary contact, but it is not confirmed "
                    "they hold final purchasing authority alone.")
    if req_id in known:
        return f"On record: {known[req_id].get('value')}."
    return "No confirmed information on record yet."


def _focus_approach(meta: dict, merchant: dict) -> str:
    q = meta.get("question", "")
    if q:
        return f"Ask: \u201c{q}\u201d"
    return f"Confirm {meta.get('label', 'this requirement').lower()} with the merchant directly."


def meeting_analysis(merchant_id: str) -> dict | None:
    """Return the mock extraction set for a merchant, or None if none exists."""
    from services import load_extractions
    return load_extractions().get(merchant_id)


def draft_follow_up(merchant: dict, gaps: list[dict]) -> str:
    """Draft a follow-up message to the merchant for unresolved requirements."""
    labels = ", ".join(f'"{g["label"]}"' for g in gaps) if gaps else "the remaining open items"
    if OPENAI_KEY:
        prompt = (
            f"Draft a short, professional follow-up email to {merchant['name']} asking to resolve these "
            f"discovery items before onboarding can proceed: {labels}. 3-4 sentences, plain text."
        )
        out = _chat([{"role": "user", "content": prompt}])
        if out:
            return out.strip()
    return (
        f"Hi there,\n\nThank you for your time earlier. Before we hand off to the onboarding team, we need "
        f"to confirm a few remaining details: {labels}. If you can share those at your convenience, we can "
        f"keep everything on track for a smooth go-live.\n\nThanks,\nMaya Chen"
    )
