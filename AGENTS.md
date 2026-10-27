# AGENTS.md

Notes for AI coding agents working in this repo. Read [docs/design.md](docs/design.md) before changing behavior.

## Project status

Part 3.2 is built: paced breathing runs end to end. Part 3.3 adds STOP and the cognitive reframe: add their text to `content/skills.js`, set `available: true`, and add one component each (reuse `ExerciseFrame.vue` and `composables/useExerciseSession.js`). Code deviations from the 3.1 design are listed in docs/design.md §l.

## Stack

- `frontend/`: Vue 3 + Vite, plain `fetch`, no router library, no state library.
- `backend/`: FastAPI, raw `sqlite3` (no ORM), `httpx` for model calls.
- SQLite file `backend/skills.db`: gitignored, created on first run.
- Model API key in `.env` (gitignored). Never commit keys.

## Folder layout

```
backend/
  main.py            # thin FastAPI routes only
  db.py              # schema (sessions, messages, feedback), connection helper
  sessions.py        # session/feedback/history logic, "usual skill" derivation
  model_client.py    # single LLM-call wrapper: system prompt, 5 s wall-clock timeout, output check, fallback, mock modes
  crisis.py          # supplementary phrase check, runs before any model call
  config.py          # settings from backend/.env
  scripts/           # live_latency.py, api_checks.sh, show_db.py
  tests/             # pytest; model always mocked; fixtures/mock_responses.json
shared/
  crisis_phrases.json        # the one phrase list (backend + frontend)
frontend/src/
  App.vue                    # root layout: CrisisButton + CrisisPanel outside every screen
  api.js                     # fire-and-forget writes, sendBeacon, acknowledgment request
  timing.js                  # breathing schedule + exercise clock (pure)
  composables/useExerciseSession.js  # session record, timing, "left" on pagehide
  content/skills.js          # ALL skill step text and timings (source of truth)
  content/crisis.js          # static crisis resources
  content/crisisKeywords.js  # matcher over shared/crisis_phrases.json
  components/
    EntryScreen.vue  SkillPicker.vue  CheckIn.vue  DoneScreen.vue  HistoryView.vue
    BreathingSkill.vue       # StopSkill.vue and ReframeSkill.vue come in 3.3
    ExerciseFrame.vue        # wraps every exercise step: Stop exercise + step
    CrisisButton.vue  CrisisPanel.vue
frontend/tests/              # vitest
docs/
```

## Hard safety constraints (do not violate)

1. **Crisis access never depends on the backend or the model.** `CrisisPanel.vue` and `CrisisButton.vue` import only `content/crisis.js`. No `fetch` and no awaits. They must render with the backend stopped.
2. **The Crisis support button is visible on every screen**, including inside exercises, during loading, and on error states.
3. **The model never writes skill steps, advice, diagnoses, or therapeutic claims.** All step text lives in `frontend/src/content/skills.js`. Model output is shown only in the acknowledgment slot.
4. **One step per screen.** Do not combine steps, and do not add menus or dashboards inside an exercise.
5. **"Stop exercise" is always visible inside an exercise.** No confirmation dialog, and no guilt wording. It saves the session as `exited_early` and continues even if that save fails.
6. **Guided exercise ≤ 90 s at intended pace**, from first instruction to final planned step, app delays included. Never force a user to finish or leave when a timer expires.
7. **No diagnostic, clinical, or therapy language. No cheerful or praising language.** The app must not imply that anyone is monitoring the user.
8. **Model calls time out at 5 s.** On any failure, show the fixed fallback text and keep the exercise going.
9. **Never auto-start a skill.** Suggestions are labels only. The user taps to start.
10. The keyword check is a **supplement**. Never describe it, or a system prompt, as the safety mechanism.

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
```

PowerShell equivalents for Windows are in the README.

## Testing expectations

- Routine automated tests use **mocked model responses** (patch the wrapper in `model_client.py`). Never make live calls in the test suite.
- Required checks: model timeout → fallback text; model error → fallback; disallowed output (too long, banned words) → fallback; Stop exercise → `exited_early=1`; crisis panel renders with the backend down; "usual skill" derivation.
- Keep live-model checks separate and labeled. Peer testing stays mocked by default, with a cap of 50 live calls per session, then revert to mocks.
- Use fictional scenarios only.
