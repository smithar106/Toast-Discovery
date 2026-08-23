"""Onboarding handoff generation.

The handoff is assembled deterministically from the structured discovery record.
Sources are tracked per field (CRM / Rep confirmed / AI extracted + confirmed)
to make the provenance of every line visible.
"""
from __future__ import annotations

from services import load_verticals
from services.discovery_engine import active_requirements


def _answer_text(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _source_of(entry) -> str:
    if not isinstance(entry, dict):
        return "Rep confirmed"
    src = entry.get("source", "rep")
    if src == "crm":
        return "CRM"
    if src == "ai":
        return "AI extracted / rep confirmed" if entry.get("confirmed") else "AI extracted"
    return "Rep confirmed"


def build_handoff(merchant: dict, answers: dict, notes: str = "", summary: str = "") -> dict:
    vname = load_verticals().get(merchant["vertical"], {}).get("name", merchant["vertical"])
    known = merchant.get("known", {})

    confirmed_answers = {
        req_id: entry
        for req_id, entry in answers.items()
        if isinstance(entry, dict) and entry.get("value") not in (None, "", [], "Unknown")
    }

    critical_items = []
    important_items = []
    open_questions = []
    for r in active_requirements(merchant["vertical"], answers):
        entry = answers.get(r["id"])
        answered = isinstance(entry, dict) and entry.get("value") not in (None, "", [], "Unknown")
        item = {
            "id": r["id"],
            "label": r["label"],
            "value": _answer_text(entry.get("value")) if answered else "—",
            "source": _source_of(entry) if answered else "Not captured",
        }
        if r.get("priority") == "critical":
            critical_items.append(item)
        else:
            important_items.append(item)
        if not answered and r.get("priority") != "critical":
            open_questions.append({"label": r["label"], "value": "To follow up", "source": "Open"})

    open_questions = open_questions[:5]

    dm = merchant.get("decision_maker") or {}
    pc = merchant.get("primary_contact") or {}

    return {
        "merchant": merchant["name"],
        "vertical": vname,
        "locations": merchant.get("locations", 1),
        "region": merchant.get("region", ""),
        "stage": merchant.get("stage", "Discovery"),
        "rep_id": merchant.get("rep_id", ""),
        "meeting_date": merchant.get("meeting_date", ""),
        "opportunity_value": merchant.get("opportunity_value", 0),
        "overview": {
            "Merchant": merchant["name"],
            "Vertical": vname,
            "Locations": merchant.get("locations", 1),
            "Region": merchant.get("region", ""),
            "Primary contact": f"{pc.get('name','—')} · {pc.get('role','')} · {pc.get('email','')}",
            "Decision maker": f"{dm.get('name','—')} ({dm.get('role','')}) — {'confirmed' if dm.get('confirmed') else 'to confirm'}",
            "Target timeline": next(
                (v.get("value") for k, v in answers.items() if k == "timeline"), "Not set"
            ),
        },
        "critical": critical_items,
        "important": important_items,
        "open_questions": open_questions,
        "notes": notes.strip() if notes.strip() else merchant.get("notes", ""),
        "known_context": [{"label": k, "value": v.get("value"), "source": v.get("source", "crm")} for k, v in known.items()],
        "summary": summary,
        "sources": {
            "CRM": sum(1 for v in confirmed_answers.values() if v.get("source") == "crm"),
            "Rep confirmed": sum(1 for v in confirmed_answers.values() if v.get("source") == "rep"),
            "AI extracted / rep confirmed": sum(1 for v in confirmed_answers.values() if v.get("source") == "ai" and v.get("confirmed")),
        },
    }
