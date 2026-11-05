# AGENTS.md

Notes for AI coding agents working in this repo. Read [docs/design.md](docs/design.md) before changing behavior.

## Project status

The app is called Tidebreak. Part 3.3 is complete: paced breathing, STOP, and the cognitive reframe; the optional "Talk it through" chat; one local profile; History; and the check-in on Home. Every departure from the 3.1 design is in docs/design.md §l. Evaluation is in docs/evaluation.md.

## Stack

- `frontend/`: Vue 3 + Vite, plain `fetch`, no router library, no state library.
- `backend/`: FastAPI, raw `sqlite3` (no ORM), `httpx` for model calls.
- SQLite file `backend/skills.db`: gitignored, created on first run.
- Model API key in `.env` (gitignored). Never commit keys.

## Folder layout

```
backend/
  main.py            # thin FastAPI routes only
  db.py              # schema, PRAGMA user_version migration, connection helper
  sessions.py        # session/feedback/history logic, learned "usual skill", reflection, delete-all
  chat.py            # Talk it through: conversations, crisis check first, model context
  profile.py         # the one local profile: stored choices + derived usual skill and counts
  model_client.py    # single LLM wrapper: prompts, 5 s wall-clock deadline, output checks, fallbacks, mock modes
  crisis.py          # supplementary phrase check, runs before any model call
  config.py          # settings from backend/.env
  scripts/           # seed_demo.py, show_db.py, api_checks.sh, and labelled live checks (live_*.py, compare_models.py, diag_server_path.py)
  tests/             # pytest; model always mocked; fixtures/mock_responses.json
shared/
  crisis_phrases.json        # the one phrase list (backend + frontend)
  skills.json                # skill labels and purpose lines (frontend + chat context)
frontend/src/
  App.vue                    # root layout: TabBar + CrisisPanel outside every screen
  api.js                     # fire-and-forget writes, sendBeacon, acknowledgment, reflection, chat, profile
  timing.js                  # schedules + exercise clock (pure)
  composables/useExerciseSession.js  # session record, timing, crisis pause, "left" on pagehide
  content/skills.js          # ALL skill step text and timings (source of truth)
  content/crisis.js          # static crisis resources
  content/crisisKeywords.js  # matcher over shared/crisis_phrases.json
  components/
    HomeScreen.vue  ActivitiesScreen.vue  ChatScreen.vue  ProfileScreen.vue  HistoryView.vue
    CheckIn.vue  DoneScreen.vue  PageHeader.vue  TabBar.vue  AppIcon.vue
    BreathingSkill.vue  StopSkill.vue  ReframeSkill.vue
    StepSequence.vue         # shared one-step-per-screen sequence (STOP, reframe)
    ExerciseFrame.vue        # exercise header, no navigation
    CrisisButton.vue  CrisisPanel.vue   # static content only
frontend/tests/              # vitest
e2e/                         # Playwright: harness.mjs, screens.mjs (axe), evaluate.mjs
docs/
```

## Hard safety constraints (do not violate)

1. **Crisis access never depends on the backend or the model.** `CrisisPanel.vue` and `CrisisButton.vue` import only `content/crisis.js`. No `fetch` and no awaits. They must render with the backend stopped.
2. **The Crisis tab is visible on every screen**, including inside exercises, during loading, and on error states. During an exercise and on the Overwhelmed Home, it is the only tab. Opening it pauses a running exercise; closing returns to the same point.
3. **The model never writes skill steps, advice, diagnoses, or therapeutic claims.** All step text lives in `frontend/src/content/skills.js`. Model output is shown only in the acknowledgment slot, the reframe reflection, and chat bubbles. In chat the model may *offer* a skill; it never starts or changes one.
4. **One step per screen.** Do not combine steps, and do not add menus or dashboards inside an exercise.
5. **"Stop exercise" is always visible inside an exercise.** No confirmation dialog, and no guilt wording. It saves the session as `stopped` (`exited_early = 1`) and continues even if that save fails.
6. **Guided exercise ≤ 90 s at intended pace**, from first instruction to final planned step, app delays included. Never force a user to finish or leave when a timer expires.
7. **No diagnostic, clinical, or therapy language. No cheerful or praising language.** The app must not imply that anyone is monitoring the user.
8. **Model calls time out at 5 s.** On any failure, show the fixed fallback text and keep the exercise going.
9. **Never auto-start a skill.** Suggestions are labels only. The user taps to start. The check-in is chosen by the user; the app never infers it.
10. **Typed reframe and STOP text is never stored.** It stays in component memory. Only the reframe's step-3 answer is sent, once, for the reflection, and neither it nor the reply is stored.
11. The keyword check is a **supplement**. Never describe it, or a system prompt, as the safety mechanism.

## Commands (macOS, bash/zsh)

```bash
# backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev            # if 8000 is taken: API_PORT=8010 npx vite --port 5180

# tests
cd backend && .venv/bin/python -m pytest
cd frontend && npm test

# browser checks (temp DB, OS-assigned ports)
cd e2e && npm install && npx playwright install chromium
node screens.mjs && node evaluate.mjs
```

PowerShell equivalents for Windows are in the README.

## Local servers (agents)

Prefer `e2e/harness.mjs`: it asks the OS for ports, uses a temp database, and stops only its own children. Otherwise check a port is free first and abort if it is busy, use `SKILLS_DB_PATH` in a temp folder, never write to `backend/skills.db`, never reuse ports given to the user, and stop only processes you started, by PID. This rule comes from two real incidents; see docs/evidence-log.md.

## Testing expectations

- Routine automated tests use **mocked model responses** (patch the wrapper in `model_client.py`). Never make live calls in the test suite.
- Required checks: model timeout → fallback text; model error → fallback; disallowed output (too long, banned words) → fallback; Stop exercise → `exited_early=1`; crisis panel renders with the backend down; "usual skill" derivation; crisis check before any model call; typed reframe and STOP text never stored.
- Keep live-model checks separate and labeled. Peer testing stays mocked by default, with a cap of 50 live calls per session, then revert to mocks.
- Use fictional scenarios only.
