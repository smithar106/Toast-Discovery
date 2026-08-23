# Toast Retail Discovery

A working Streamlit prototype built for a Toast case study interview. It turns merchant discovery from a generic post-meeting checklist into a **prescriptive, vertical-specific playbook** that tells a sales rep exactly what they cannot afford to leave without knowing.

> **All merchant, rep, and operational data in this repository is fictional mock data created for the case study. No real Toast or merchant data is used.**

---

## Product thesis

The highest-leverage problem is not better post-meeting note-taking. It is preventing implementation-critical information from being missed **while the sales rep still has access to the merchant**.

> Don't design the process around getting a second meeting.

The central principle: **know what you cannot afford to leave without knowing.**

Two ideas govern the architecture:

1. **Minimum-sufficient discovery** — the system decides what "complete" means for *this* merchant (vertical, scale, conditional answers), not a one-size-fits-all form.
2. **Deterministic rules own critical outcomes** — an LLM interprets and prioritizes; deterministic Python decides whether required information is complete. AI output is labeled and never silently satisfies a critical requirement.

---

## What the prototype demonstrates

| Capability | Where |
| --- | --- |
| Weekly merchant meeting list with completeness signals | Sales Rep → This Week |
| Vertical-specific discovery playbooks (5 verticals) | Sales Rep → merchant playbook |
| Conditional questions that react to earlier answers | Any playbook |
| CRM-known info prepopulated, never re-entered | Playbook header |
| "Before you leave" critical-gap blocking | Submission gate |
| Recording upload + simulated AI fact extraction (labeled, needs confirmation) | Additional context |
| Deterministic completeness %, blocked/enabled submission | Submission gate |
| Onboarding handoff with per-field provenance | Post-submit artifact |
| Executive KPIs, week-over-week trends, segmentation filters | Control Center |
| Reactive KPIs — KPI row recomputes when you segment | Control Center |
| Critical-gap analysis, vertical & rep performance | Control Center |
| Governed requirements library + governance activity | Control Center |
| Insight panel ("what I'd investigate this week") | Control Center |

**Flagship demo:** *Route 9 Fuel & Grab.* The merchant is 90% there but **age verification was never discussed** — the exact failure that historically caused rework and escalation. The playbook makes the gap impossible to miss, the rep answers it, conditional questions appear, discovery completes, and the onboarding handoff explicitly carries the confirmed age-verification requirement.

---

## Architecture

```
Mock Salesforce / Merchant Data
            ↓
        Python App (Streamlit)
            ↓
Requirements Library + optional OpenAI API
            ↓
 Prioritized Discovery Playbook
            ↓
      Streamlit UI (widgets → structured answers)
            ↓
        Deterministic Validation
            ↓
    Mock Salesforce Update → Onboarding Handoff
```

```
Toast-Discovery/
├── app.py                      # entry point, sidebar role selector
├── requirements.txt
├── Procfile                    # Railway start command
├── runtime.txt
├── .env.example
├── .gitignore
│
├── views/
│   ├── sales_rep.py            # View 1
│   └── control_center.py       # View 2
│
├── components/
│   ├── ui.py                   # shared visual system
│   ├── merchant_card.py
│   ├── discovery_form.py       # conditional widget rendering
│   ├── metrics.py              # KPIs + Plotly charts
│   └── handoff.py              # handoff artifact renderer
│
├── services/
│   ├── __init__.py             # data loading
│   ├── discovery_engine.py     # requirement assembly + conditions
│   ├── validation.py           # deterministic completeness rules
│   ├── ai_service.py           # optional LLM + demo fallback
│   └── handoff_service.py      # handoff generation
│
├── data/
│   ├── merchants.json          # fictional merchants + seeded CRM/discovery state
│   ├── requirements.json       # governed requirements library
│   ├── verticals.json          # vertical metadata
│   ├── reps.json               # fictional sales reps
│   ├── metrics.json            # KPI targets, insights, governance events
│   └── records.json            # generated mock operational records
│
├── scripts/
│   ├── generate_records.py     # deterministic mock record generator (data tool)
│   └── run_tests.py            # smoke tests
└── assets/
```

### Build vs. buy — the story the code supports

- **Buy / integrate commodity capabilities:** Salesforce, calendar, transcription, Slack, LLM infrastructure, analytics infrastructure.
- **Build the differentiated intelligence layer:** governed vertical requirements, minimum-sufficient-discovery logic, contextual prioritization, deterministic completeness validation, handoff generation, and the operational feedback loop.

The code is organized to keep that boundary visible: `requirements.json` is the governed library, `validation.py` is deterministic, and `ai_service.py` is the only optional/LLM-touching surface.

---

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/smithar106/Toast-Discovery.git
cd Toast-Discovery
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run app.py
```

Open the printed URL. **No API key is required** — the app runs fully offline with deterministic demo fallbacks.

### Run the smoke tests

```bash
python scripts/run_tests.py
```

Covers the Route 9 walkthrough, deterministic validation, the AI-confirmation rule, handoff generation, and Control Center segmentation reactivity.

### Optional: enable LLM features

Copy `.env.example` to `.env` and set a real key. Streamlit does not auto-load `.env`, so either export the variable before running:

```bash
export OPENAI_API_KEY=sk-...
streamlit run app.py
```

When a key is present, the LLM powers contextual "what matters most" summaries and recording fact extraction. Without a key, equivalent rule-based fallbacks keep the demo fully functional. In both cases:

- AI-generated facts are labeled **AI extracted** and only count once the rep confirms them.
- Critical requirements are satisfied by **rep/crm answers only** — never by unconfirmed AI output.

---

## Deploying to Railway

1. Push this repository to GitHub.
2. In Railway, **New Project → Deploy from GitHub repo** → select `Toast-Discovery`.
3. Railway auto-detects the `Procfile` and `requirements.txt`. No extra build steps.
4. Optional: add an `OPENAI_API_KEY` variable in the service's **Variables** tab (leave unset for offline mode).
5. Railway assigns a public URL automatically.

Start command (used by `Procfile`):

```
streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true
```

`runtime.txt` pins Python 3.12 for a consistent build.

---

## Demo walkthrough (5–7 minutes)

1. **Sales Rep view** — see "This Week": five merchants with statuses and completeness.
2. **Open Route 9 Fuel & Grab.**
3. Review **Already Known (from CRM)** chips — decision maker, locations, fuel context.
4. See prioritized **🔴 Critical requirements**; **Age verification is visually unresolved**.
5. Answer the age-restricted question → **conditional questions appear** (product categories, today's method, POS enforcement).
6. Add a **merchant note** and optionally **upload a recording** (simulated AI extraction, labeled, needs confirmation).
7. Watch **Discovery completeness** climb; **Before you leave** clears.
8. **Submit Discovery** → Salesforce update, structured record saved, handoff generated, consultant notified.
9. The **onboarding handoff** shows the confirmed age-verification requirement with provenance (CRM / Rep / AI).
10. Switch to **RevOps Director → Control Center**.
11. Read the **executive KPI row** and week-over-week trend charts.
12. **Filter to Convenience + Fuel** — charts, tables, and the KPI row react.
13. **Critical gap analysis** shows age verification as the most commonly missed requirement.
14. Open **Governed Discovery Requirements** — see owners, versions, and rules; explain how leadership closes the loop.

---

## Product rules enforced in code

1. Not a generic CRM — vertical-first playbooks.
2. Not every field is mandatory — only critical, applicable requirements block.
3. Minimum sufficient discovery per merchant (conditions evaluated from answers).
4. Vertical-specific requirements are central (`requirements.json`).
5. Known CRM info is prepopulated and flagged, never re-entered.
6. AI reduces cognitive load — short context summaries, candidate facts.
7. Deterministic logic governs critical completeness (`validation.py`).
8. AI facts never silently satisfy critical requirements (confirmed flag required).
9. The rep sees exactly what remains before leaving ("Before you leave").
10. The Director dashboard surfaces whether the system creates measurable value.

---

## Prototype limitations

- All data is **fictional mock data** (merchants, reps, metrics, records).
- Recording upload stores/transcribes only in simulation; real transcription/extraction would plug into `ai_service.extract_facts_from_text`.
- Submission writes to in-memory session state, not Salesforce.
- Control Center records are pre-generated (`scripts/generate_records.py`); they are not fed by live rep submissions.
- No auth — role is selected from the sidebar.

## Production architecture considerations

- Replace mock data modules with a real data layer (Salesforce sync, data warehouse, or backend API).
- Move the requirements library into a versioned, governable config store with change control.
- Persist discovery records to a database; make the Control Center read from the same source of truth as submission.
- Add real transcription (e.g., rev/deepgram) and pass transcripts through a structured fact-extraction pipeline with human confirmation.
- Add auth/roles (rep vs. RevOps), audit logging for governance edits, and CI for the requirements library.
