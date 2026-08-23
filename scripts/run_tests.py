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
    sub = [b for b in at.button if b.label == "Submit discovery"][0]
    assert sub.disabled is True, "submission must be blocked with critical gaps"
    print("  ui: submission blocked initially = True")

    [x for x in at.multiselect if x.key == "ans_route9_age_products"][0].set_value(["Tobacco"]).run()
    [x for x in at.radio if x.key == "ans_route9_age_verification_today"][0].set_value("Scanner at register").run()
    [x for x in at.button_group if x.key == "ans_route9_age_pos_enforced"][0].set_value("Yes").run()
    sub = [b for b in at.button if b.label == "Submit discovery"][0]
    assert sub.disabled is False, "submission must enable once critical gaps closed"
    print("  ui: submission enabled after answering chain = True")

    [x for x in at.text_area if x.key == "notes_route9"][0].set_value("Compliance is top priority.").run()
    sub = [b for b in at.button if b.label == "Submit discovery"][0]
    sub.click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Discovery submitted" in " ".join(s.value for s in at.success)
    assert "Salesforce opportunity updated" in md
    assert "Information provenance" in md
    assert "age verification" in md.lower()
    print("  ui: submit -> handoff with confirmations + age verification = True")


def test_control_center():
    at = stt.AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.radio[0].set_value("RevOps").run()
    assert not at.exception
    assert len(at.selectbox) == 5, "vertical, rep, region, size, week filters"
    assert "Governed requirements" not in " ".join(m.value for m in at.markdown)
    # week filter present + reacts
    weekbox = [s for s in at.selectbox if s.label == "Week"][0]
    weekbox.set_value("08/02/2026").run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "submitted discoveries in this view" in md, "week filter updates record count"
    # vertical filter + dataframes render
    [x for x in at.selectbox if x.label == "Vertical"][0].set_value("Convenience + Fuel").run()
    assert not at.exception
    assert len(at.dataframe) >= 1
    print("  control center: renders + segmentation filters react = True")


def test_revenue_optimization_flow():
    from services.optimization import ranked_drivers, friction_score, annual_opportunity, load_drivers

    drivers = ranked_drivers("All")
    assert drivers[0]["id"] == "age_verification", "age verification should rank first"
    assert annual_opportunity(drivers[0]) > 0

    # every vertical must surface drivers and every driver must have a full option pipeline
    from services import load_verticals
    for vk, vmeta in load_verticals().items():
        assert ranked_drivers(vmeta["name"]), f"no drivers for {vmeta['name']}"
    for d in load_drivers():
        assert len(d["options"]) >= 2, f"driver {d['id']} needs >=2 options"

    at = stt.AppTest.from_file("app.py", default_timeout=30)
    at.run()
    at.radio[0].set_value("RevOps").run()
    at.radio[0].set_value("Revenue Optimization Plan").run()
    assert not at.exception
    # vertical filter
    [x for x in at.selectbox if x.label == "Vertical"][0].set_value("Convenience + Fuel").run()
    assert not at.exception
    # open age verification detail
    [x for x in at.button if x.key == "opt_open_age_verification"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Current state" in md and "OPTION 1" in md and "OPTION 3" in md
    # select approach
    [x for x in at.button if x.key == "opt_select_strengthen_playbook"][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Proposed optimization" in md and "Primary constraint" in md
    # send draft plan
    [x for x in at.button if "Send Draft Project Plan" in x.label][0].click().run()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "Preview project plan" in md
    assert "Optimization decisions" in md and "Draft plan sent" in md
    assert "fictional case-study assumptions" in md
    print("  revenue optimization: landing -> detail -> options -> decision -> plan -> history = True")


if __name__ == "__main__":
    tests = [test_deterministic_validation, test_ai_facts_need_confirmation,
             test_handoff_includes_age_verification, test_route9_ui_walkthrough,
             test_control_center, test_revenue_optimization_flow]
    for t in tests:
        t()
    print("\nAll prototype tests passed.")
