"""Requirement and merchant data loading."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(filename: str) -> Any:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_requirements() -> list[dict]:
    return _load("requirements.json")["requirements"]


def load_verticals() -> dict:
    return _load("verticals.json")["vertical_meta"]


def load_merchants() -> list[dict]:
    return _load("merchants.json")["merchants"]


def load_crm_context() -> dict:
    return _load("crm_context.json")["crm_context"]


def load_extractions() -> dict:
    return _load("extractions.json")["extractions"]


def get_merchant(merchant_id: str) -> dict | None:
    for m in load_merchants():
        if m["id"] == merchant_id:
            return m
    return None
