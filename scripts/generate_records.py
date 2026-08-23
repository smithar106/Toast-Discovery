"""Deterministic mock record generator for the Control Center.

Generates a stable, reproducible set of submitted discovery records so the
dashboard's segmentation filters actually filter real rows. Run once to produce
data/records.json (the app reads only the committed JSON, so this is purely a
data-generation tool).

    python scripts/generate_records.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

random.seed(42)

WEEKS = [
    ("2026-06-14", "06/14/2026"),
    ("2026-06-21", "06/21/2026"),
    ("2026-06-28", "06/28/2026"),
    ("2026-07-05", "07/05/2026"),
    ("2026-07-12", "07/12/2026"),
    ("2026-07-19", "07/19/2026"),
    ("2026-07-26", "07/26/2026"),
    ("2026-08-02", "08/02/2026"),
    ("2026-08-09", "08/09/2026"),
    ("2026-08-16", "08/16/2026"),
    ("2026-08-23", "08/23/2026"),
]

VERTICALS = {
    "grocery": "Grocery",
    "convenience_fuel": "Convenience + Fuel",
    "specialty_food": "Specialty Food",
    "meat_seafood": "Meat & Seafood",
    "general_retail": "General Retail",
}

REPS = [
    ("maya_chen", "Maya Chen", "Northeast"),
    ("jordan_ellis", "Jordan Ellis", "Southeast"),
    ("priya_raman", "Priya Raman", "Midwest"),
    ("dev_patel", "Dev Patel", "Southwest"),
    ("sofia_reyes", "Sofia Reyes", "West"),
    ("tom_okafor", "Tom Okafor", "Texas"),
]

# baseline miss probabilities per vertical (improve over time)
BASE_FIRST_PASS = {
    "grocery": 0.84, "convenience_fuel": 0.76, "specialty_food": 0.88,
    "meat_seafood": 0.86, "general_retail": 0.80,
}
BASE_CLARIFICATION = {
    "grocery": 0.12, "convenience_fuel": 0.18, "specialty_food": 0.09,
    "meat_seafood": 0.10, "general_retail": 0.13,
}

SIZES = [(1, "1 location"), (2, "2–5 locations"), (3, "2–5 locations"), (4, "2–5 locations"), (6, "6+ locations"), (8, "6+ locations")]

RECORDS = []
record_id = 0

for week_idx, (week, label) in enumerate(WEEKS):
    improvement = week_idx * 0.015  # steady system-wide improvement
    ttl_improvement = week_idx * 0.6  # downstream go-live speed-up as discovery improves
    for vert_key, vert_label in VERTICALS.items():
        for rep_id, rep_name, region in REPS:
            n_deals = random.randint(3, 9)
            for _ in range(n_deals):
                record_id += 1
                size_val, size_label = random.choice(SIZES)
                fp_base = min(BASE_FIRST_PASS[vert_key] + improvement, 0.96)
                cl_base = max(BASE_CLARIFICATION[vert_key] - improvement * 0.5, 0.05)
                first_pass = random.random() < fp_base
                clarification = (not first_pass) or random.random() < cl_base
                tth = max(0.9, round(random.gauss(1.9, 0.5) + (0.4 if clarification else 0), 1))
                ttl = max(8, round(random.gauss(19, 3) + (2.5 if clarification else 0) - ttl_improvement))
                reengage = 1 if (clarification and random.random() < 0.55 - improvement * 0.6) else 0
                gaps = random.randint(0, 3) if not first_pass else 0
                RECORDS.append({
                    "id": record_id,
                    "week": week,
                    "week_label": label,
                    "week_index": week_idx,
                    "vertical": vert_key,
                    "vertical_label": vert_label,
                    "rep_id": rep_id,
                    "rep": rep_name,
                    "region": region,
                    "size": size_val,
                    "size_label": size_label,
                    "first_pass": first_pass,
                    "clarification": clarification,
                    "critical_gaps": gaps,
                    "time_to_handoff": tth,
                    "time_to_live": ttl,
                    "reengagement": reengage,
                })

out = {"generated": True, "records": RECORDS}

# Keep the dataset a clean, stable total (drop oldest records if needed so the
# headline count reads 2026, matching the data year).
TARGET = 2026
if len(RECORDS) > TARGET:
    RECORDS = RECORDS[len(RECORDS) - TARGET:]
    out["records"] = RECORDS
    for i, r in enumerate(RECORDS):
        r["id"] = i + 1

(ROOT / "data" / "records.json").write_text(json.dumps(out, indent=2))
print(f"wrote {len(RECORDS)} records to data/records.json")
