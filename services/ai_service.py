"""Optional AI service.

LLM is used only for interpretation and contextualization. The demo must work
without any API key: every function falls back to deterministic, rule-based
behavior that still produces useful output. AI-derived facts are always labeled
and never silently satisfy critical requirements (see validation._is_confirmed).
"""
from __future__ import annotations

import json
import os

from services import load_extractions, load_verticals

API_KEY = (
    os.environ.get("DEEPSEEK_API_KEY")
    or os.environ.get("AI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or ""
)
MODEL = os.environ.get("TOAST_LLM_MODEL") or os.environ.get("AI_MODEL") or "deepseek-chat"
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("AI_BASE_URL") or "https://api.deepseek.com"


def ai_available() -> bool:
    return bool(API_KEY)


def _chat(messages: list[dict], json_mode: bool = False) -> str | None:
    if not API_KEY:
        return None
    try:
        import openai

        client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
        kwargs = {"model": MODEL, "messages": messages, "temperature": 0.2}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
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

    if not API_KEY:
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
    if not API_KEY:
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
    if not API_KEY:
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
# Sales Rep — meeting focus, analysis, follow-up (AI with deterministic fallback)
# ---------------------------------------------------------------------------

def _requirement_meta(req_id: str) -> dict:
    from services import load_requirements
    for r in load_requirements():
        if r["id"] == req_id:
            return r
    return {"id": req_id, "label": req_id, "rule": "", "question": ""}


def meeting_focus(merchant: dict, answers: dict, critical_missing: list[dict]) -> dict:
    """Build the contextual 'focus for this meeting' block for a merchant.

    Returns a dict with:
      - objective: 1-2 sentence meeting objective grounded in remaining criticals
      - priorities: 1-3 items, each with what_we_know / suggested_approach / why_it_matters
    The governed requirement is deterministic; the guidance is the LLM contextualizing
    it for THIS merchant. Deterministic fallback is used when no API key is present.
    """
    priorities = []
    for req in critical_missing[:3]:
        meta = _requirement_meta(req["id"])
        priorities.append({
            "req_id": req["id"],
            "requirement": meta.get("label", req["id"]),
            "what_we_know": _focus_what_we_know(merchant, req["id"]),
            "suggested_approach": _focus_approach(meta, merchant, req["id"]),
            "why_it_matters": meta.get("rule", "Required for a complete sales-to-onboarding handoff."),
        })

    n_missing = len(critical_missing)
    if n_missing == 1:
        objective = (
            f"Leave the call with enough information to complete the discovery handoff. "
            f"One critical requirement remains unresolved: {critical_missing[0]['label']}."
        )
    elif n_missing:
        labels = ", ".join(r["label"] for r in critical_missing)
        objective = (
            f"Leave the call with enough information to complete the discovery handoff. "
            f"{n_missing} critical requirements remain unresolved: {labels}."
        )
    else:
        objective = (
            "All critical requirements are already confirmed. Use the meeting to confirm "
            "important context and the target timeline."
        )

    if API_KEY and priorities:
        req_text = "; ".join(p["requirement"] for p in priorities)
        known_text = "; ".join(f"{k}: {v.get('value')}" for k, v in merchant.get("known", {}).items())
        prompt = (
            f"For merchant {merchant['name']} ({merchant['vertical']}), produce JSON: "
            f"{{'objective': 'one sentence', 'priorities': [{{'requirement','what_we_know',"
            f"'suggested_approach','why_it_matters'}}]}} for a discovery meeting. Unresolved requirements: "
            f"{req_text}. Known context: {known_text}. Suggested approaches are natural, direct questions the "
            f"rep can ask the merchant. Plain JSON only."
        )
        out = _chat([{"role": "user", "content": prompt}], json_mode=True)
        if out:
            try:
                start, end = out.find("{"), out.rfind("}") + 1
                data = json.loads(out[start:end])
                if isinstance(data, dict) and data.get("priorities"):
                    return {
                        "objective": data.get("objective", objective),
                        "priorities": data["priorities"][:3],
                    }
            except Exception:
                pass
    return {"objective": objective, "priorities": priorities}


def _focus_what_we_know(merchant: dict, req_id: str) -> str:
    from services import load_crm_context
    known = merchant.get("known", {})
    ctx = load_crm_context().get(merchant["id"], {}).get("facts", [])
    if req_id == "decision_maker":
        dm = merchant.get("decision_maker") or {}
        # use crm_context facts about decision authority if available
        for f in ctx:
            if "decision" in f["label"].lower():
                return f"{f['value']}. Listed as co-owner; final purchasing authority is not yet confirmed."
        if dm.get("name"):
            return (f"{dm['name']} is the primary contact, but it is not confirmed "
                    "they hold final purchasing authority alone.")
    if req_id in known:
        return f"On record: {known[req_id].get('value')}."
    return "No confirmed information on record yet."


def _focus_approach(meta: dict, merchant: dict, req_id: str = "") -> str:
    from services import load_crm_context
    ctx = load_crm_context().get(merchant["id"], {}).get("facts", [])
    if req_id == "decision_maker":
        dm = merchant.get("decision_maker") or {}
        if dm.get("name"):
            return (
                f"{dm['name']} appears to be driving the evaluation, so avoid asking generically who the "
                f"decision maker is. Instead confirm the process naturally: \u201cIf we land on the right "
                f"configuration today, is there anyone else who needs to be involved before you can move "
                f"forward?\u201d"
            )
    q = meta.get("question", "")
    if q:
        return f"Ask: \u201c{q}\u201d"
    return f"Confirm {meta.get('label', 'this requirement').lower()} with the merchant directly."


def meeting_analysis(merchant: dict, transcript: str = "") -> dict:
    """Extract discovery evidence from meeting context.

    When an OpenAI key is present, the LLM reads the transcript/notes and returns
    structured candidate facts + a summary, grounded in this merchant's governed
    requirements. Without a key (or on failure), the pre-authored mock extraction
    set is returned so the demo always works offline.
    """
    mock = load_extractions().get(merchant["id"]) or {"extractions": [], "gaps": []}

    if not API_KEY or not transcript.strip():
        return mock

    from services import load_requirements
    reqs = [r for r in load_requirements() if r.get("vertical") in ("all", merchant["vertical"])]
    req_summary = "; ".join(
        f"{r['id']} = {r['label']}" for r in reqs[:24]
    )

    prompt = (
        f"You are assisting a Toast sales rep. Merchant: {merchant['name']} "
        f"({merchant['vertical']}, {merchant.get('locations', 1)} locations).\n\n"
        f"These are the governed discovery requirements for this merchant type:\n{req_summary}\n\n"
        f"Below is the rep's meeting context (notes and/or a simulated transcript). "
        f"Extract candidate answers ONLY where the text provides evidence.\n\n"
        f"Meeting context:\n{transcript[:6000]}\n\n"
        f"Return JSON with exactly two keys:\n"
        f"  'summary': a 2-3 sentence plain-text meeting summary.\n"
        f"  'extractions': a list of {{'req_id','label','suggested_value','evidence','confidence'}} "
        f"where req_id is one of the requirement ids above and evidence is a short quote from the context. "
        f"Do NOT invent facts that are not in the context. If nothing is supported, return an empty list.\n"
        f"Plain JSON only."
    )
    out = _chat([{"role": "user", "content": prompt}], json_mode=True)
    if out:
        try:
            start, end = out.find("{"), out.rfind("}") + 1
            data = json.loads(out[start:end])
            extractions = data.get("extractions", []) or []
            return {
                "summary": data.get("summary", ""),
                "extractions": [
                    {
                        "req_id": e.get("req_id", ""),
                        "label": e.get("label", e.get("req_id", "Extracted item")),
                        "suggested_value": e.get("suggested_value", ""),
                        "evidence": e.get("evidence", ""),
                        "confidence": e.get("confidence", "medium"),
                    }
                    for e in extractions[:8]
                    if e.get("req_id") and e.get("suggested_value")
                ],
                "gaps": [],
            }
        except Exception:
            pass
    return mock


def draft_follow_up(merchant: dict, gaps: list[dict]) -> str:
    """Draft a follow-up message to the merchant for unresolved requirements."""
    labels = ", ".join(f'"{g["label"]}"' for g in gaps) if gaps else "the remaining open items"
    if API_KEY:
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
