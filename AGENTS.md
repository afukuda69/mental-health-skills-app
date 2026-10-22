# AGENTS.md

Notes for AI coding agents working in this repo. Read [docs/design.md](docs/design.md) before changing behavior.

## Project status

Part 3.1 (design) only: there is no application code yet. Part 3.2 builds paced breathing end to end. Part 3.3 adds STOP and the cognitive reframe.

## Stack

- `frontend/`: Vue 3 + Vite, plain `fetch`, no router library, no state library.
- `backend/`: FastAPI, raw `sqlite3` (no ORM), `httpx` for model calls.
- SQLite file `backend/skills.db`: gitignored, created on first run.
- Model API key in `.env` (gitignored). Never commit keys.

## Planned folder layout

```
backend/
  main.py            # thin FastAPI routes only
  db.py              # schema (sessions, messages, feedback), connection helper
  sessions.py        # session/feedback/history logic, "usual skill" derivation
  model_client.py    # single LLM-call wrapper: system prompt, 5s timeout, output check, fallback
  tests/             # pytest; model always mocked
frontend/src/
  App.vue
  content/skills.js          # ALL skill step text and timings (source of truth)
  content/crisis.js          # static crisis resources
  content/crisisKeywords.js  # supplementary keyword list
  components/
    EntryScreen.vue  SkillPicker.vue  CheckIn.vue  DoneScreen.vue  HistoryView.vue
    BreathingSkill.vue  StopSkill.vue  ReframeSkill.vue
    ExerciseFrame.vue        # wraps every exercise step: Stop exercise + Crisis support
    CrisisButton.vue  CrisisPanel.vue
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

## PowerShell commands (planned, Windows)

```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev

# tests
cd backend; .\.venv\Scripts\Activate.ps1; python -m pytest
```

## Testing expectations

- Routine automated tests use **mocked model responses** (patch the wrapper in `model_client.py`). Never make live calls in the test suite.
- Required checks: model timeout → fallback text; model error → fallback; disallowed output (too long, banned words) → fallback; Stop exercise → `exited_early=1`; crisis panel renders with the backend down; "usual skill" derivation.
- Keep live-model checks separate and labeled. Peer testing stays mocked by default, with a cap of 50 live calls per session, then revert to mocks.
- Use fictional scenarios only.
