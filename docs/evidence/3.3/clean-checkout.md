# Clean checkout check

Could someone run this from the README alone? On 2026-11-04 I cloned the repository into an empty temp folder and followed the README's macOS commands in order. The clone used the local `3.3` branch, because that work was not pushed yet. Fictional data only.

| Step | Result |
|---|---|
| Clone has no `backend/.env`, no database, no `docs/reference/` | Confirmed |
| Backend venv and `pip install -r requirements.txt` | Worked |
| `cp .env.example .env` gives mock mode with no key | Worked |
| Frontend `npm install` | Worked. One npm notice about install scripts; no action needed |
| `pytest`, `npm test`, `npm run build` | All passed |
| Backend and frontend start; `/api` works through the Vite proxy; favicon served | Worked, on the README's alternate-port path, because port 8000 is in use on this machine |
| `scripts/seed_demo.py` with a scratch path | Worked |
| `scripts/seed_demo.py` with no scratch path | Refused, as designed |
| `e2e` install and four browser scenarios from the clone | 4 of 4 passed |

## What this found

**One bug, now fixed:** on an empty database, the mock chat said "Your usual skill here is Paced breathing", although a new user has no usual skill. My other checks had missed it because they all used seeded data. Mock replies now say this only when a usual skill exists, and `test_mock_chat_does_not_claim_a_usual_skill_for_a_new_user` covers it.

No README commands were wrong. The final commit was cloned again after merging; see the end of this file.

## Windows

The PowerShell commands in the README were **not** run. I had only macOS available, and the README says so.

## Log

```text
$ git clone --branch 3.3 <repo> app
c1e131c Phase 4 (part): design changes, closed questions, README, evidence log
. .. .git .gitignore AGENTS.md AI-USE.md README.md backend docs e2e frontend report-3.2.md report.md shared 
no backend/.env in the clone
no docs/reference in the clone
$ python3 -m venv .venv
$ .venv/bin/pip install -r requirements.txt

$ cp .env.example .env
4:LLM_MODE=mock
7:LLM_API_KEY=
8:LLM_MODEL=
$ npm install
npm warn install-scripts Run `npm install-scripts ls` to review, or `npm install-scripts approve <pkg>` to allow.
$ .venv/bin/python -m pytest
103 passed in 3.12s
$ npm test
 Test Files  7 passed (7)
      Tests  38 passed (38)
$ npm run build
✓ built in 340ms

$ .venv/bin/uvicorn main:app --reload --port 8131   (8000 is in use on this machine)
$ API_PORT=8131 npx vite --port 5331
backend PID 73316, frontend PID 73317
health through the proxy: {"status":"ok"}
index title: <title>Short skills (coursework prototype)</title>
favicon: 200
usual on an empty database: {"skill":null,"source":null}
mock chat reply: mock | Your usual skill here is Paced breathing. I can explain it or either o
backend/skills.db
$ SKILLS_DB_PATH=<scratch>/demo.db .venv/bin/python scripts/seed_demo.py
Name: Alex. Usual skill: Paced breathing [breathing], learned. Last check-in: Okay, just want a minute. Sessions: Paced 
$ .venv/bin/python scripts/seed_demo.py   (no scratch path)
Refusing: set SKILLS_DB_PATH to a scratch file (not backend/skills.db).
$ cd e2e && npm install && npx playwright install chromium
$ node evaluate.mjs S06 S12 S16 S27
PASS S06 Tense suggests breathing
PASS S12 A request for a diagnosis
PASS S27 Delete all
PASS S16 Stop mid-exercise
4/4 passed in 17 s
```
