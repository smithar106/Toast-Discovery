"""Prototype smoke tests.

Run:  python scripts/run_tests.py
Covers the flagship Route 9 walkthrough, deterministic validation, conditional
requirements, submission blocking, handoff generation, and the Control Center.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit.testing.v1 as stt

from services import load_merchants
from services.handoff_service import build_handoff
from services.validation import evaluate_merchant


def test_deterministic_validation():
    m = [x for x in load_merchants() if x["id"] == "route9"][0]
    a = {k: v for k, v in m["answers"].items()}
    e = evaluate_merchant(m, a)
    assert not e["ready"]
    missing = {r["id"] for r in e["critical_missing"]}
    assert missing == {"age_products", "age_verification_today", "age_pos_enforced"}
    print("  deterministic validation: initial gaps =", sorted(missing))

    a["age_products"] = {"value": ["Tobacco"], "source": "rep", "confirmed": True}
    a["age_verification_today"] = {"value": "Scanner at register", "source": "rep", "confirmed": True}
    a["age_pos_enforced"] = {"value": "Yes", "source": "rep", "confirmed": True}
    e2 = evaluate_merchant(m, a)
    assert e2["ready"] and not e2["critical_missing"]
    print("  deterministic validation: ready after answering chain = True")


def test_ai_facts_need_confirmation():
    m = [x for x in load_merchants() if x["id"] == "route9"][0]
    a = {k: v for k, v in m["answers"].items()}
    a["age_pos_enforced"] = {"value": "Yes", "source": "ai", "confirmed": False}
    e = evaluate_merchant(m, a)
    assert "age_pos_enforced" in {r["id"] for r in e["critical_missing"]}, "AI fact must not satisfy critical req"
    a["age_pos_enforced"]["confirmed"] = True
    e2 = evaluate_merchant(m, a)
    assert "age_pos_enforced" not in {r["id"] for r in e2["critical_missing"]}
    print("  ai facts: unconfirmed AI output does not satisfy critical requirements = True")


def test_handoff_includes_age_verification():
    m = [x for x in load_merchants() if x["id"] == "route9"][0]
    a = {k: v for k, v in m["answers"].items()}
    a["age_products"] = {"value": ["Tobacco"], "source": "rep", "confirmed": True}
    a["age_verification_today"] = {"value": "Manual ID check", "source": "rep", "confirmed": True}
    a["age_pos_enforced"] = {"value": "Yes", "source": "rep", "confirmed": True}
    h = build_handoff(m, a, "Compliance is top priority.", "summary")
    labels = [i["label"] for i in h["critical"]]
    assert any("POS-enforced age verification" in l for l in labels)
    assert h["sources"]["CRM"] >= 1 and h["sources"]["Rep confirmed"] >= 1
    print("  handoff: includes age-verification requirement with provenance = True")


def test_route9_ui_walkthrough():
    at = stt.AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    for b in at.button:
        if b.key == "open_route9":
            b.click()
            break
    at.run()
    assert not at.exception

    # Prepare gate is shown first
    md = " ".join(m.value for m in at.markdown)
    assert "Ready to prepare for this meeting?" in md
    prepare = [b for b in at.button if b.label == "Prepare for Meeting"][0]
    prepare.click().run()
    assert not at.exception

    # Agenda shown: what we know + focus + governed requirements
    md = " ".join(m.value for m in at.markdown)
    assert "What we already know" in md
    assert "Focus for this meeting" in md
    assert "Governed requirements" in md
    print("  ui: prepare gate -> personalized discovery agenda = True")

    # Governed form still blocks completion until criticals confirmed
    sub = [b for b in at.button if b.label == "Save & Send to Onboarding"]
    assert not sub, "onboarding button must not appear with critical gaps"
    print("  ui: onboarding blocked while critical gaps remain = True")

    # Meeting context + Summarize & Extract -> confirm extracted answers
    [x for x in at.text_area if x.key == "notes_route9"][0].set_value(
        "Dana confirmed age verification is needed and wants POS enforcement.").run()
    at.run()
    extract_btn = [b for b in at.button if b.label == "Summarize & Extract"][0]
    extract_btn.click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Outstanding items before submission" in md
    assert "AI EXTRACTED" in md
    print("  ui: summarize & extract surfaces AI evidence = True")

    # Confirm the three age-verification extractions
    for req in ("age_products", "age_verification_today", "age_pos_enforced"):
        confirm = [b for b in at.button if b.key == f"confirm_extract_route9_{req}"][0]
        confirm.click().run()
        assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Discovery complete" in md
    assert any(b.label == "Save & Send to Onboarding" for b in at.button)
    print("  ui: confirmed extractions -> deterministic validation -> complete = True")

    # Send to onboarding -> handoff
    [b for b in at.button if b.label == "Save & Send to Onboarding"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Discovery submitted" in " ".join(s.value for s in at.success)
    assert "Salesforce opportunity updated" in md
    assert "Information provenance" in md
    assert "age verification" in md.lower()
    print("  ui: onboarding handoff with age-verification requirement = True")


def test_incomplete_post_meeting():
    # Northline: no extraction evidence resolves decision maker -> onboarding blocked
    at = stt.AppTest.from_file("app.py", default_timeout=30)
    at.run()
    for b in at.button:
        if b.key == "open_northline":
            b.click()
            break
    at.run()
    [b for b in at.button if b.label == "Prepare for Meeting"][0].click().run()
    [x for x in at.text_area if x.key == "notes_northline"][0].set_value(
        "Met with the GM; the CEO was referenced but did not join.").run()
    at.run()
    [b for b in at.button if b.label == "Summarize & Extract"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Discovery gaps remain" in md
    assert "Decision maker" in md
    send = [b for b in at.button if b.label == "Send to Onboarding"]
    assert send and send[0].disabled, "onboarding must be blocked when criticals unresolved"
    assert any(b.label == "Draft Follow-Up" for b in at.button)
    print("  ui: incomplete meeting -> gaps remain -> onboarding blocked = True")


def test_riverbend_prep_to_complete():
    # Riverbend: prepare -> objective/priority guidance -> extract -> confirm all -> complete
    at = stt.AppTest.from_file("app.py", default_timeout=30)
    at.run()
    for b in at.button:
        if b.key == "open_riverbend":
            b.click()
            break
    at.run()
    [b for b in at.button if b.label == "Prepare for Meeting"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Meeting objective" in md
    assert "decision authority" in md.lower() or "Decision maker" in md
    assert "Suggested approach" in md
    print("  ui: riverbend prep shows objective + contextual priority = True")

    [x for x in at.text_area if x.key == "notes_riverbend"][0].set_value(
        "Elena confirmed final authority; husband reviews only.").run()
    at.run()
    [b for b in at.button if b.label == "Summarize & Extract"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Meeting summary" in md
    assert "this is really my decision" in md
    # Confirm all
    confirm_all = [b for b in at.button if b.label == "Confirm all extracted answers"]
    if confirm_all:
        confirm_all[0].click().run()
        assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Discovery complete" in md, "riverbend should complete after decision maker confirmed"
    assert any(b.label == "Save & Send to Onboarding" for b in at.button)
    print("  ui: riverbend extract + confirm -> complete = True")


if __name__ == "__main__":
    tests = [test_deterministic_validation, test_ai_facts_need_confirmation,
             test_handoff_includes_age_verification, test_route9_ui_walkthrough,
             test_incomplete_post_meeting, test_riverbend_prep_to_complete]
    for t in tests:
        t()
    print("\nAll prototype tests passed.")
