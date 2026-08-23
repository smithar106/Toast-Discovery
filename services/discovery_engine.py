"""Discovery engine: vertical-specific requirement assembly + condition evaluation.

Deterministic core. The LLM never decides what counts as a critical gap; these
rules do. Answers are keyed by requirement id and may carry a source
(CRM / Rep / AI-extracted) and confirmation flag.
"""
from __future__ import annotations

from typing import Any

from services import load_requirements


def _answer_value(answers: dict, field: str) -> Any:
    entry = answers.get(field)
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def condition_met(condition: dict | None, answers: dict) -> bool:
    """Evaluate a requirement condition against current answers."""
    if not condition:
        return True
    field = condition.get("field")
    op = condition.get("op", "equals")
    target = condition.get("value")
    actual = _answer_value(answers, field)

    if op == "equals":
        return actual == target
    if op == "not_equals":
        return actual != target
    if op == "gt":
        try:
            return float(actual) > float(target)
        except (TypeError, ValueError):
            return False
    if op == "contains":
        if isinstance(actual, list):
            return target in actual
        if isinstance(actual, str):
            return target in actual.split(",")
        return False
    return True


def active_requirements(vertical: str, answers: dict) -> list[dict]:
    """Requirements that apply to this vertical and whose conditions are met."""
    out = []
    for req in load_requirements():
        if req.get("vertical") not in ("all", vertical):
            continue
        if condition_met(req.get("condition"), answers):
            out.append(req)
    return out


def grouped_requirements(vertical: str, answers: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (critical, important, context) requirements for a merchant."""
    active = active_requirements(vertical, answers)
    critical = [r for r in active if r.get("priority") == "critical"]
    important = [r for r in active if r.get("priority") == "important"]
    return critical, important, []
