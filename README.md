# Mental Health Skills Prototype (Assignment 3)

> **Coursework prototype only.** This is a Penn State course project. It is not therapy, not a diagnostic tool, and not a mental health support service. It does not monitor anyone. Do not use it, or recommend it to anyone, as something to rely on in a difficult moment. All testing uses fictional scenarios.
>
> If you are in crisis in the US: call or text **988** (Suicide & Crisis Lifeline), text **HOME to 741741** (Crisis Text Line), or call **911** in an emergency.

## Purpose

A small localhost app that guides one short, structured skill at a time:

- **Paced breathing (4-in / 6-out)**: core skill, built in Part 3.2
- **STOP**: added in Part 3.3
- **One-minute cognitive reframe**: added in Part 3.3

The app controls each skill's steps, timing, exits, saved state, and crisis access. A language model only writes short, neutral acknowledgments. The design is based on the study findings R1–R4 and D1–D6 in Assignment 3 overview (Canvas).

## Stack

- Frontend: Vue 3 + Vite (`frontend/`)
- Backend: FastAPI + raw `sqlite3` (`backend/`)
- Storage: SQLite file `backend/skills.db`, created on first run (gitignored)
- Model: OpenRouter, called only from the backend
- Runs on localhost only

## Crisis resources are US-only

The Crisis support panel lists US services (988, Crisis Text Line, 911). It is a static part of the frontend, so it works with the backend or model down. Nobody monitors this app.

## Run it (macOS / Linux, bash or zsh)

Needs Python 3.11+ and Node 18+. From a clean checkout:

```bash
# Terminal 1: backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # mock mode works with no key
.venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                      # open http://localhost:5173
```

The Vite dev server forwards `/api` to the backend. If port 8000 or 5173 is taken:

```bash
.venv/bin/uvicorn main:app --reload --port 8010    # backend
API_PORT=8010 npx vite --port 5180                  # frontend
```

## Settings (`backend/.env`)

| Variable | Values | Default |
|---|---|---|
| `LLM_MODE` | `mock`, `live`, `mock_error`, `mock_timeout`, `mock_malformed` | `mock` |
| `LLM_API_KEY` | OpenRouter key (live only) | empty |
| `LLM_MODEL` | OpenRouter model id (live only) | empty |
| `LLM_REASONING` | `off`, `on` (let the model reason first; slower) | `off` |
| `LLM_MAX_CALLS` | live calls per server run, then mock | `50` |
| `SKILLS_DB_PATH` | SQLite file path | `backend/skills.db` |

`backend/.env` is gitignored. Never commit a key.

**Switching mock and live:** set `LLM_MODE` in `backend/.env`, or override it for one run. A real environment variable wins over the file:

```bash
LLM_MODE=live .venv/bin/uvicorn main:app --port 8000
LLM_MODE=mock_timeout .venv/bin/uvicorn main:app --port 8000   # simulate a slow model
```

The failure modes always show the fixed fallback text. `mock_timeout` waits the full 5 s.

**Model choice:** the tested default is `nvidia/nemotron-3-ultra-550b-a55b:free` with `LLM_REASONING=off` (about 2–3 s per reply). `nvidia/nemotron-3.5-lightning:free` is faster (about 0.3 s) but its replies are vaguer. See [docs/evidence/3.2/server-path-diagnosis.md](docs/evidence/3.2/server-path-diagnosis.md).

## Tests

All automated tests use mocked model responses. No network calls.

```bash
cd backend && .venv/bin/python -m pytest      # 64 tests
cd frontend && npm test                        # 8 tests (vitest)
```

Look at the database:

```bash
backend/.venv/bin/python backend/scripts/show_db.py
```

## Windows (PowerShell) equivalents

```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev

# tests
cd backend; .\.venv\Scripts\Activate.ps1; python -m pytest
cd frontend; npm test

# one-off mode override
$env:LLM_MODE = "mock_error"; uvicorn main:app --port 8000
# other ports
$env:API_PORT = "8010"; npx vite --port 5180
```

## Project layout

```
backend/   main.py (routes) · sessions.py (logic) · db.py (schema) · model_client.py · crisis.py · config.py
           scripts/ (live latency, endpoint checks, DB dump) · tests/ (pytest, fixtures/)
frontend/  src/App.vue · src/content/ (all step text, crisis resources) · src/components/ · src/timing.js · tests/
shared/    crisis_phrases.json (the one phrase list, read by backend and frontend)
docs/      design.md · reused.md · evidence-log.md · evidence/3.2/
```

## Documents

| File | Contents |
|---|---|
| [docs/design.md](docs/design.md) | Main design, open questions, and "Changes since 3.1" |
| [docs/reused.md](docs/reused.md) | What is adapted from the travel app / RAG chatbot |
| [docs/evidence-log.md](docs/evidence-log.md) | Curated evidence log |
| [docs/evidence/3.2/](docs/evidence/3.2/) | Test output, endpoint and browser runs, live latency, manual checklist |
| [AGENTS.md](AGENTS.md) | Rules for coding agents |
| [AI-USE.md](AI-USE.md) | AI tool disclosure |
| [report.md](report.md) | Part 3.1 submission |
| [report-3.2.md](report-3.2.md) | Part 3.2 submission |
