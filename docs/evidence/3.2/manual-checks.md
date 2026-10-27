# Manual browser checks (Part 3.2)

Run these in a real browser (Chrome) with DevTools open (Console and Network tabs). Save screenshots in `docs/evidence/3.2/manual/` with the filenames given, and fill in the **Observed** column. Use fictional input only.

The automated run in [browser-run.md](browser-run.md) already covered checks 1, 3, 4, 5, 8, 9 and 10 in headless Chromium. Checks 2 (live) and 6 (tab close) could not be automated.

## Setup (bash/zsh, from the repo root)

```bash
# Terminal 1: backend (mock mode unless a check says otherwise)
cd backend
LLM_MODE=mock .venv/bin/uvicorn main:app --port 8000

# Terminal 2: frontend
cd frontend
npm run dev            # http://localhost:5173
```

If port 8000 or 5173 is already in use, use other ports:

```bash
LLM_MODE=mock .venv/bin/uvicorn main:app --port 8010    # backend
API_PORT=8010 npx vite --port 5180                       # frontend -> http://localhost:5180
```

To restart the backend in another mode, press Ctrl+C in terminal 1 and rerun the command with a different `LLM_MODE` (`mock`, `live`, `mock_error`, `mock_timeout`, `mock_malformed`).

Look at the database (terminal 3, repo root):

```bash
backend/.venv/bin/python backend/scripts/show_db.py      # all three tables
sqlite3 backend/skills.db "SELECT id, skill, end_reason, measured_ms, pauses_ms, crisis_ms, planned_ms, steps_completed FROM sessions ORDER BY id DESC LIMIT 3;"
sqlite3 backend/skills.db "SELECT id, session_id, role, model_status, latency_ms, crisis_flag, text FROM messages ORDER BY id DESC LIMIT 3;"
```

To start from an empty database, stop the backend and run `rm backend/skills.db`.

## Checks

| # | Steps | Expected | DB check | Screenshot | Observed |
|---|---|---|---|---|---|
| 1 | Backend `mock`. Open the app, tap **Tense or wound up**, then **Paced breathing**. Don't touch anything until **Continue** appears. | Intro text, then the circle with "In"/"Out" and "1 of 7" … "7 of 7", then the closing text. Console: `[timing] setup_ms=…` at the start and `[timing] exercise measured_ms=≈75000 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed` at the closing. | `sqlite3 backend/skills.db "SELECT end_reason, measured_ms, planned_ms, steps_completed FROM sessions ORDER BY id DESC LIMIT 1;"` → `completed`, same measured_ms as the console, `75000`, `7` | `01-full-run-console.png` (closing screen + console) | |
| 2a | Same as 1 (mock). On the closing screen, note the text. | Mock text: "You came in feeling tense and took seven slow breaths." Console `[model] acknowledgment status=mock`. | `sqlite3 backend/skills.db "SELECT role, model_status, text FROM messages ORDER BY id DESC LIMIT 1;"` → `model`, `mock` | `02a-ack-mock.png` | |
| 2b | Restart the backend with `LLM_MODE=live`. Run breathing once more. If you get the fallback, try up to 2 more times (each run is 1 live call; cap is 50). | Either model text (console `status=ok latency_ms=…`) or, if the model took over 5 s, the fallback "That was seven slow breaths." (console `status=timeout`). Both are correct behavior. Record which. | `sqlite3 backend/skills.db "SELECT role, model_status, latency_ms, text FROM messages ORDER BY id DESC LIMIT 3;"` | `02b-ack-live.png` | |
| 3 | Stop the backend (Ctrl+C). Reload the app. Tap **Crisis support**, then **Back to where I was**. Start breathing and let it run to the end. | Crisis panel opens with 988 / 741741 / 911. No "Use my usual" button. Breathing runs normally. Closing shows "That was seven slow breaths." Console shows `[session] write failed` warnings, and the UI doesn't break. | none (backend stopped) | `03-backend-down-crisis.png`, `03-backend-down-closing.png` | |
| 4a | Backend `LLM_MODE=mock_error`. Run breathing to the end. | Closing shows "That was seven slow breaths." right away. Crisis support is visible. | `… messages … LIMIT 1` → `fallback`, `error` | `04a-mock-error.png` | |
| 4b | Backend `LLM_MODE=mock_timeout`. Run breathing to the end. | Same fallback text. The request takes 5 s but starts at "7 of 7", so the closing isn't delayed. Crisis support is visible. | `… messages … LIMIT 1` → `fallback`, `timeout`, latency ≈5005 | `04b-mock-timeout.png` | |
| 5 | Backend `mock`. Start breathing; at about "2 of 7" tap **Stop exercise**. | Goes straight to "Stopped. That's fine." No dialog, no check-in. Console `[timing] … end_reason=stopped`. | `… sessions … LIMIT 1` → `stopped`, measured_ms ≈ console | `05-stopped.png` | |
| 6 | Backend `mock`. Start breathing; at about "2 of 7" **close the tab** (Cmd+W). | Tab closes. | `… sessions … LIMIT 1` → `left`, measured_ms filled. (Repeat with switching to another tab and coming back: the exercise is paused with **Resume**; the row shows `left` until the exercise finishes, then `completed`.) | `06-left-db.png` (terminal) | |
| 7 | Backend `mock`. The crisis phrase check only runs on typed text, and 3.2 has no typed input in the UI (the reframe is 3.3). Check it through the API in terminal 3: `curl -s -X POST localhost:8000/api/sessions -H 'Content-Type: application/json' -d '{"client_id":"manual-crisis","skill":"reframe"}' > /dev/null; curl -s -X POST localhost:8000/api/sessions/manual-crisis/messages -H 'Content-Type: application/json' -d '{"text":"Fictional test phrase: I want to die"}'` | Response: `"status":"scripted","crisis":true` with the scripted reply. Backend terminal shows no `model_client` log line for this request. | `sqlite3 backend/skills.db "SELECT role, text, model_status, crisis_flag FROM messages ORDER BY id DESC LIMIT 2;"` → user row with empty text and `crisis_flag=1`, then a scripted row with `crisis_flag=1` | `07-crisis-phrase-api.png` | |
| 8 | Backend `mock`. Start breathing. At "2 of 7" tap **Crisis support**, wait about 10 s, tap **Back to where I was**. Let it finish. | Circle and counter freeze while the panel is open and continue from the same point. Console: `crisis_ms≈10000`, `measured_ms≈75000`. | `… sessions … LIMIT 1` → crisis_ms ≈ 10000, measured_ms ≈ 75000 | `08-crisis-pause.png` | |
| 9 | After the runs above, on the entry screen tap **History**. Tap **Show message** on one row. | Rows: date · Paced breathing · Finished / Stopped early / Left the page. Message text only after the tap. No scores, no streaks. | `backend/.venv/bin/python backend/scripts/show_db.py` | `09-history.png` | |
| 10 | Back to start. | "Use my usual: Paced breathing" button (derived from history: most recent Helped, otherwise most completed). Tapping it starts the intro directly; nothing starts by itself. | `curl -s localhost:8000/api/usual` → `{"skill":"breathing"}` | `10-usual.png` | |

Extra, optional: in macOS System Settings → Accessibility → Display, turn on **Reduce motion** and run breathing. The circle stays still, and the label plus a seconds countdown carry the pace. Screenshot: `11-reduced-motion.png`.
