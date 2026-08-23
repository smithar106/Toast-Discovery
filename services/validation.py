"""Deterministic validation of discovery completeness.

Rules (not an LLM) decide whether critical information is complete:
  * A critical, required requirement is incomplete when its answer is missing,
    empty, 'Unknown', an empty list, or a blank string.
  * Non-required important items never block submission.
"""
from __future__ import annotations

from typing import Any

from services.discovery_engine import active_requirements

UNKNOWN_VALUES = {"unknown", "Unknown", "", None}


def _is_answered(entry: Any) -> bool:
    if isinstance(entry, dict):
        value = entry.get("value")
    else:
        value = entry
    if isinstance(value, list):
        return len(value) > 0
    if value in UNKNOWN_VALUES:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, list) and not value:
        return False
    return True


def _is_confirmed(entry: Any) -> bool:
    """AI-extracted facts must be explicitly confirmed before they count."""
    if not isinstance(entry, dict):
        return True
    if entry.get("source") == "ai" and not entry.get("confirmed"):
        return False
    return True


def evaluate_merchant(merchant: dict, answers: dict) -> dict:
    """Compute completeness for a merchant. Returns a structured result."""
    active = active_requirements(merchant["vertical"], answers)

    critical = [r for r in active if r.get("priority") == "critical" and r.get("required")]
    important = [r for r in active if r.get("priority") == "important"]

    critical_complete = [
        r for r in critical if _is_answered(answers.get(r["id"])) and _is_confirmed(answers.get(r["id"]))
    ]
    critical_missing = [r for r in critical if r not in critical_complete]
    important_missing = [r for r in important if not _is_answered(answers.get(r["id"]))]

    total_scored = len(critical) + len(important)
    complete_scored = len(critical_complete) + (len(important) - len(important_missing))
    pct = round(100 * complete_scored / total_scored) if total_scored else 100

    return {
        "critical_total": len(critical),
        "critical_complete": len(critical_complete),
        "critical_missing": critical_missing,
        "important_missing": important_missing,
        "total_scored": total_scored,
        "complete_scored": complete_scored,
        "completeness_pct": pct,
        "ready": len(critical_missing) == 0,
    }


def critical_gaps(merchant: dict, answers: dict) -> list[dict]:
    return evaluate_merchant(merchant, answers)["critical_missing"]


def completeness_pct(merchant: dict, answers: dict) -> int:
    return evaluate_merchant(merchant, answers)["completeness_pct"]
