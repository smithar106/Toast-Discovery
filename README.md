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
| Weekly merchant meeting agenda with critical-item counts | Sales → This Week |
| "Prepare for Meeting" — simulated agenda build | Sales → merchant playbook |
| What we already know (provenance + status badges) | Discovery agenda |
| Focus for this meeting — meeting objective + contextual priorities | Discovery agenda |
| Governed requirements (deterministic) with source badges | Discovery agenda |
| Collapsible requirement sections (dropdowns) | Discovery playbook |
| Vertical-specific discovery playbooks (5 verticals) | Sales → merchant playbook |
| Conditional questions that react to earlier answers | Any playbook |
| CRM-known info prepopulated, never re-entered | Playbook header |
| "Before you leave" critical-gap blocking | Submission gate |
| Critical-remaining as the primary rep metric (not %) | Playbook header + agenda |
| Summarize & Extract — AI evidence → rep Confirm/Edit | Meeting analysis |
| Confirm all extracted answers | Meeting analysis |
| Meeting summary from unstructured context | Meeting analysis |
| Unconfirmed AI output never satisfies critical requirements | Meeting analysis |
| Incomplete meeting → Discovery gaps remain → onboarding blocked | Meeting analysis |
| Draft Follow-Up for unresolved items | Meeting analysis |
| Onboarding handoff with per-field provenance | Post-submit artifact |
| "How this works" — AI vs deterministic boundary | Discovery agenda expander |

**Flagship demo:** *Route 9 Fuel & Grab.* The merchant is 90% there but **age verification was never discussed** — the exact failure that historically caused rework and escalation. The playbook makes the gap impossible to miss; after the meeting the rep runs **Summarize & Extract**, confirms the extracted age-verification answers, and deterministic validation flips discovery to complete — and the onboarding handoff explicitly carries the confirmed requirement.

**Riverbend Grocery:** a second full path where one critical item (decision authority) is unresolved before the meeting; the prep guidance suggests a natural approach, and after the meeting extraction confirms Elena Boyd's authority → discovery completes.

---

## Architecture

```
GOVERNED TOAST REQUIREMENTS        MERCHANT CONTEXT
"What must we know?"               CRM + notes + merchant information
        ↓                                    ↓
 Deterministic requirements engine        LLM interpretation
        ↓                                    ↓
STRUCTURED DISCOVERY STATE (confirmed / inferred / unknown)
        ↓
 Deterministic validation → remaining gaps
        ↓
 LLM contextualization → PERSONALIZED DISCOVERY AGENDA
        ↓
       Sales Rep conducts discovery
        ↓
 NOTES / RECORDING → LLM extraction → REP CONFIRMATION
        ↓
 Deterministic validation
        ↓
 Complete → onboarding   OR   Incomplete → resolve gaps
```

The LLM interprets ambiguity. Deterministic logic governs the process. The rep remains in control.

```
Toast-Discovery/
├── app.py                      # entry point
├── requirements.txt
├── Procfile                    # Railway start command
├── runtime.txt
├── .env.example
├── .gitignore
│
├── views/
│   └── sales_rep.py            # the Sales Rep experience
│
├── components/
│   ├── ui.py                   # shared visual system
│   ├── merchant_card.py        # agenda row
│   ├── discovery_form.py       # collapsible governed requirement sections
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
│   ├── crm_context.json        # known facts with provenance + certainty status
│   ├── extractions.json        # mock AI extraction evidence + unresolved gaps
│   ├── requirements.json       # governed requirements library (deterministic)
│   └── verticals.json          # vertical metadata
│
├── scripts/
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

Covers the Route 9 and Riverbend walkthroughs, deterministic validation, the AI-confirmation rule, handoff generation, and the blocked-onboarding path.

### Optional: enable LLM features

Copy `.env.example` to `.env` and set a real key. Streamlit does not auto-load `.env`, so either export the variable before running:

```bash
export OPENAI_API_KEY=sk-...
streamlit run app.py
```

When a key is present, the LLM powers contextual meeting guidance, meeting summaries, and extraction language. Without a key, equivalent rule-based fallbacks keep the demo fully functional. In both cases:

- AI-generated facts are labeled **AI ASSISTED** and only count once the rep confirms them.
- Critical requirements are satisfied by **rep/crm confirmed answers only** — never by unconfirmed AI output.

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

## Demo walkthrough

1. See the **Discovery agenda** — merchant rows with time, vertical, status, and **critical items to confirm**. Green (complete) accounts need no intervention; red accounts carry unresolved critical discovery.
2. **Open Route 9 Fuel & Grab** (red). The header reads "3 critical requirements remaining."
3. **Prepare for Meeting** — see "What we already know" (with CONFIRMED / EXTRACTED / NEEDS CONFIRMATION badges), the **Meeting objective**, and **Focus for this meeting** contextual priorities.
4. The **🔴 Critical requirements** section is a set of collapsible dropdowns. Age verification is impossible to miss.
5. After the meeting, add notes/recording → **Summarize & Extract**.
6. **Outstanding items before submission** — review the AI-extracted evidence, then **Confirm** (or Edit) each item, or **Confirm all**.
7. Deterministic validation flips to **Discovery complete** → **Save & Send to Onboarding**.
8. The **onboarding handoff** shows the confirmed requirement with provenance (CRM / Rep / AI).
9. **Riverbend Grocery** demonstrates the prep guidance ("is there anyone else who needs to be involved…?") and the same extract → confirm → complete path.
10. **Northline** demonstrates the blocked path: no extraction evidence for decision maker → **Discovery gaps remain** → **Draft Follow-Up**, onboarding disabled.

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
10. The demo shows whether the system keeps reps focused on the deals where intervention changes the outcome.

---

## Prototype limitations

- All data is **fictional mock data** (merchants, reps, CRM context, extraction evidence).
- Recording upload stores/transcribes only in simulation; real transcription/extraction would plug into `ai_service`.
- Submission writes to in-memory session state, not Salesforce.
- Extraction evidence is pre-authored mock data, not generated from real audio.
- No auth.

## Production architecture considerations

- Replace mock data modules with a real data layer (Salesforce sync, data warehouse, or backend API).
- Move the requirements library into a versioned, governable config store with change control.
- Persist discovery records to a database; make any analytics read from the same source of truth as submission.
- Add real transcription (e.g., rev/deepgram) and pass transcripts through a structured fact-extraction pipeline with human confirmation.
- Add auth/roles, audit logging for requirement changes, and CI for the requirements library.
