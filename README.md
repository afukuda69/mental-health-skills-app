# Mental Health Skills Prototype (Assignment 3)

> **Coursework prototype only.** This is a Penn State course project. It is not therapy, not a diagnostic tool, and not a mental health support service. It does not monitor anyone. Do not use it, or recommend it to anyone, as something to rely on in a difficult moment. All testing uses fictional scenarios.
>
> If you are in crisis in the US: call or text **988** (Suicide & Crisis Lifeline), text **HOME to 741741** (Crisis Text Line), or call **911** in an emergency.

## Purpose

A small localhost app that guides one short, structured skill at a time:

- **Paced breathing (4 in, 6 out):** seven slow breaths, about 75 s
- **STOP:** four short prompts, about 60 s
- **Cognitive reframe:** three optional writing prompts and a reflection, about 70 s

Around them: an optional check-in on Home that changes what is suggested, an optional **"Talk it through"** chat, one local **Profile** with History inside it, and a **Crisis** tab on every screen.

The app controls each skill's steps, timing, exits, saved state, and crisis access. A language model only writes short acknowledgments, the reframe reflection, and chat replies. It never writes or changes skill steps, and it never starts a skill. The design is based on the study findings R1–R4 and D1–D6 in Assignment 3 overview (Canvas).

## Stack

- Frontend: Vue 3 + Vite (`frontend/`)
- Backend: FastAPI + raw `sqlite3` (`backend/`)
- Storage: SQLite file `backend/skills.db`, created on first run (gitignored)
- Model: OpenRouter, called only from the backend. Mock mode needs no key
- Runs on localhost only

## Crisis resources are US-only

The Crisis panel lists US services (988, Crisis Text Line, 911). It is a static part of the frontend, so it works with the backend or model down. Nobody monitors this app.

## Run it (macOS / Linux, bash or zsh)

Needs Python 3.11+ and Node 18+. From a clean checkout, starting in the repository folder:

```bash
# Terminal 1: backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # starts in mock mode; no key needed
.venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                      # open http://localhost:5173
```

The Vite dev server forwards `/api` to the backend. If port 8000 or 5173 is taken, use others:

```bash
.venv/bin/uvicorn main:app --reload --port 8010    # backend
API_PORT=8010 npx vite --port 5180                  # frontend
```

**Demo data (optional):** this fills a separate scratch database with five fictional sessions and the name "Alex", so Profile and the usual skill show something. It refuses to touch `backend/skills.db`.

```bash
cd backend
SKILLS_DB_PATH=/tmp/skills-demo.db .venv/bin/python scripts/seed_demo.py
SKILLS_DB_PATH=/tmp/skills-demo.db .venv/bin/uvicorn main:app --port 8000
```

## Settings (`backend/.env`)

| Variable | Values | Default |
|---|---|---|
| `LLM_MODE` | `mock`, `live`, `mock_error`, `mock_timeout`, `mock_malformed` | `mock` |
| `LLM_API_KEY` | OpenRouter key (live only) | empty |
| `LLM_MODEL` | OpenRouter model id (live only). Tested with `nvidia/nemotron-3-ultra-550b-a55b:free` | empty |
| `LLM_MOCK_CHAT` | chat reply in mock mode: `auto`, `normal`, `offer`, `malformed`, `overlong`, `banned` | `auto` |
| `LLM_REASONING` | `off`, `on` (let the model reason first; slower) | `off` |
| `LLM_MAX_CALLS` | live calls per server run, then mock | `50` |
| `SKILLS_DB_PATH` | SQLite file path | `backend/skills.db` |

`backend/.env` is gitignored. Never commit a key.

**Switching mock and live:** set `LLM_MODE` in `backend/.env`, or override it for one run. A real environment variable wins over the file:

```bash
LLM_MODE=live .venv/bin/uvicorn main:app --port 8000
LLM_MODE=mock_timeout .venv/bin/uvicorn main:app --port 8000   # simulate a slow model
```

The failure modes always show fixed fallback text. `mock_timeout` waits the full 5 s. Peer testing should stay in mock mode. If live calls are needed, keep `LLM_MAX_CALLS` at 50 or lower.

## What is saved

- **Sessions:** skill, times, how it ended, and optional rating.
- **Chat messages:** saved so a conversation can be reopened.
- **Profile:** optional name, usual skill (learned or chosen), motion setting, last check-in.
- **Never saved:** text typed in the reframe or the STOP note. Only the reframe's step-3 answer is sent, once, for the reflection, and neither it nor the reply is stored. Crisis-phrase text in chat is not stored either.

Everything stays in the local SQLite file. Profile has **Delete all**.

## Talk it through (chat)

- Optional. Use fictional scenarios only. Nobody monitors it.
- The crisis phrase check runs before any model call. On a match: a fixed reply, the Crisis panel opens, there is no model call, and the typed text is not stored. It is a simple list and misses indirect phrasing, so it is a supplement. The Crisis tab is the safety route.
- The model sees a fixed prompt, one line per skill (`shared/skills.json`), a profile summary (name, usual skill, last check-in, counts), and the last 10 messages of this conversation. See [the exact context](docs/evidence/3.3/chat-context-example.md).
- It must reply with JSON `{reply, offer_skill}`, at most 60 words. Anything else gives a fixed fallback with links to the three skills.

## Tests

All automated tests use mocked model responses. No network calls.

```bash
cd backend && .venv/bin/python -m pytest      # 103 tests
cd frontend && npm test                        # 38 tests (vitest)
```

Look at a database:

```bash
backend/.venv/bin/python backend/scripts/show_db.py path/to/file.db
```

**Browser checks (optional):** these start private copies of the app on OS-assigned ports with temp databases, so they can't touch a running app or your data. Install the backend and frontend first.

```bash
cd e2e
npm install
npx playwright install chromium
node evaluate.mjs        # the 28 evaluation scenarios, about 2.5 minutes
node screens.mjs         # accessibility scan and screenshots of every screen
```

## Windows (PowerShell) equivalents

These are written from the macOS commands and have **not** been run on Windows.

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
# demo data
$env:SKILLS_DB_PATH = "$env:TEMP\skills-demo.db"; python scripts\seed_demo.py
```

## Project layout

```
backend/   main.py (routes) · sessions.py · chat.py · profile.py · db.py (schema, migration) · model_client.py · crisis.py · config.py
           scripts/ (demo seed, DB dump, labelled live checks) · tests/ (pytest, fixtures/)
frontend/  src/App.vue · src/content/ (all step text, crisis resources) · src/components/ · src/timing.js · tests/
shared/    crisis_phrases.json (the one phrase list) · skills.json (skill labels and purpose lines)
e2e/       browser checks: harness.mjs, evaluate.mjs, screens.mjs
docs/      design.md · evaluation.md · reused.md · evidence-log.md · evidence/
```

## Documents

| File | Contents |
|---|---|
| [docs/design.md](docs/design.md) | Main design, closed questions, and every change since 3.1 |
| [docs/evaluation.md](docs/evaluation.md) | Scenarios, behavior checks, live checks, findings |
| [docs/reused.md](docs/reused.md) | What is adapted from the travel app / RAG chatbot |
| [docs/evidence-log.md](docs/evidence-log.md) | Curated evidence log |
| [docs/evidence/3.3/](docs/evidence/3.3/) | 3.3 test output, browser runs, accessibility scan, clean-checkout record |
| [docs/evidence/3.2/](docs/evidence/3.2/) | 3.2 evidence |
| [AGENTS.md](AGENTS.md) | Rules for coding agents |
| [AI-USE.md](AI-USE.md) | AI tool disclosure |
| [report-3.3.md](report-3.3.md) | Part 3.3 submission |
