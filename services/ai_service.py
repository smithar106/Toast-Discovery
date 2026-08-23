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
    lines = [f"For this {vname.lower()} merchant with {locs} location(s), focus discovery on the operations that drive the biggest rework risk."]
    if critical_missing:
        labels = [r["label"] for r in critical_missing]
        lines.append(f"The highest priority is confirming: {' and '.join(labels)} — these shape configuration and can't be added cleanly after sign-off.")
    else:
        lines.append("All critical requirements are covered; use remaining time to capture important context and confirm timeline.")
    if locs and int(locs) > 1:
        lines.append("Because this is a multi-location rollout, confirm whether configuration should be centralized or store-by-store.")
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
