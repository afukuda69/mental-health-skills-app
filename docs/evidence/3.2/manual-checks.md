# Manual browser checks (Part 3.2)

**Evidence:** one screen recording of all checks ([screen recording](https://drive.google.com/file/d/129JPv1-0rBF0R__5kqGLcC7qO--4IEpB/view?usp=sharing)), plus terminal output (console lines, `curl` responses, `sqlite3` results) pasted into the **Observed** column.

**UI note:** the steps below use the current look: Home with **Open practice**, a floating tab bar with **Home**, **History** and **Crisis** (only **Crisis** while breathing runs), and "Breathe in" / "Breathe out" with cycle dots and a "Cycle n of 7" caption. The Observed rows already filled in (1, 2a, 3, 5) were recorded on the earlier look. Behavior is unchanged; see [restyle-run.md](restyle-run.md).

Run these in a real browser (Chrome) with DevTools open (Console and Network tabs). Use fictional input only. The commands below use ports **8010** (backend) and **5180** (frontend). With the default ports, replace 8010 with 8000.

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

| # | Steps | Expected | DB check | Observed |
|---|---|---|---|---|
| 1 | Backend `mock`. Open the app. On Home, tap **Tense or wound up** (optional), then **Open practice**. Don't touch anything until **Continue** appears. | Intro text, then the circle with "Breathe in" / "Breathe out", the cycle dots and "Cycle 1 of 7" … "Cycle 7 of 7", then the closing text. Only the **Crisis** tab shows while breathing runs. Console: `[timing] setup_ms=…` at the start and `[timing] exercise measured_ms=≈75000 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed` at the closing. | `sqlite3 backend/skills.db "SELECT end_reason, measured_ms, planned_ms, steps_completed FROM sessions ORDER BY id DESC LIMIT 1;"` → `completed`, same measured_ms as the console, `75000`, `7` | DB: both runs `completed`, steps 7/7, planned_ms 75000, pauses_ms 0, crisis_ms 0. measured_ms **71124** (session 3) and **71084** (session 4), about 3.9 s below the 75000 planned. setup_ms 20137 / 27958, stored separately. [confirm in video: circle, "1 of 7"…"7 of 7", closing text, and the console `[timing]` line matching measured_ms] *(Recorded on the earlier look; behavior unchanged, see [restyle-run.md](restyle-run.md).)* |
| 2a | Same as 1 (mock). On the closing screen, note the text. | Mock text: "You came in feeling tense and took seven slow breaths." Console `[model] acknowledgment status=mock`. | `sqlite3 backend/skills.db "SELECT role, model_status, text FROM messages ORDER BY id DESC LIMIT 1;"` → `model`, `mock` | DB: message rows `model` / `mock`, latency_ms 1 and 0, text "You took a minute for seven slow breaths." (sessions 3, 4). That's the mock reply for entry choice `okay`, which both sessions used; the Expected column shows the reply for `tense`. [confirm in video: this text on the closing screen and the console `[model] … status=mock` line] *(Recorded on the earlier look; behavior unchanged, see [restyle-run.md](restyle-run.md).)* |
| 2b | Restart the backend with `LLM_MODE=live`. On Home, tap **Open practice** and run breathing once more. If you get the fallback, try up to 2 more times (each run is 1 live call; cap is 50). | Either model text (console `status=ok latency_ms=…`) or, if the model took over 5 s, the fallback "That was seven slow breaths." (console `status=timeout`). Both are correct behavior. Record which. | `sqlite3 backend/skills.db "SELECT role, model_status, latency_ms, text FROM messages ORDER BY id DESC LIMIT 3;"` | Verified by automated run, see [final-checks.md](final-checks.md). One live call: `model` / `ok`, latency_ms 731, measured_ms 75014, text "You completed seven slow breaths. This was your first paced breathing session." |
| 3 | Stop the backend (Ctrl+C). Reload the app. Tap the **Crisis** tab, then **Back to where I was**. Tap **Open practice** and let it run to the end. | Crisis panel opens with 988 / 741741 / 911. No "Use my usual" link under Open practice. Breathing runs normally. Closing shows "That was seven slow breaths." Console shows `[session] write failed` warnings, and the UI doesn't break. | none (backend stopped) | Not verifiable from the DB: with the backend stopped nothing is written, so no record is expected. [confirm in video: crisis panel with 988 / 741741 / 911, no "Use my usual" button, breathing runs to the end, fallback text, `[session] write failed` warnings] *(Recorded on the earlier look; behavior unchanged, see [restyle-run.md](restyle-run.md).)* |
| 4a | Backend `LLM_MODE=mock_error`. Tap **Open practice** and run breathing to the end. | Closing shows "That was seven slow breaths." right away. The **Crisis** tab is visible. | `… messages … LIMIT 1` → `fallback`, `error` | Verified by automated run, see [final-checks.md](final-checks.md). `fallback` / `error`, closing "That was seven slow breaths.", measured_ms 75001, Crisis tab visible. |
| 4b | Backend `LLM_MODE=mock_timeout`. Tap **Open practice** and run breathing to the end. | Same fallback text. The request takes 5 s but starts at "Cycle 7 of 7", so the closing isn't delayed. The **Crisis** tab is visible. | `… messages … LIMIT 1` → `fallback`, `timeout`, latency ≈5005 | Verified by automated run, see [final-checks.md](final-checks.md). `fallback` / `timeout`, latency_ms 5006, same fallback text, measured_ms 75011, Crisis tab visible. |
| 5 | Backend `mock`. Tap **Open practice**; at about "Cycle 2 of 7" tap **Stop exercise** (in the button row under the circle). | Goes straight to "Stopped. That's fine." No dialog, no check-in. Console `[timing] … end_reason=stopped`. | `… sessions … LIMIT 1` → `stopped`, measured_ms ≈ console | DB: both `stopped`, exited_early 1, steps_completed 0/7, no feedback row (no check-in saved). measured_ms 5482 with pauses_ms 950 (session 1), and 1958 (session 2). Both stops came earlier than the "2 of 7" point in the steps (about 5.5 s and 2.0 s of active time). [confirm in video: "Stopped. That's fine.", no dialog, no check-in screen, console `end_reason=stopped`] *(Recorded on the earlier look; behavior unchanged, see [restyle-run.md](restyle-run.md).)* |
| 6 | Backend `mock`. Tap **Open practice**; at about "Cycle 2 of 7" **close the tab** (Cmd+W). | Tab closes. | `… sessions … LIMIT 1` → `left`, measured_ms filled. (Repeat with switching to another tab and coming back: the exercise is paused with **Resume**; the row shows `left` until the exercise finishes, then `completed`.) | Verified by automated run, see [final-checks.md](final-checks.md). `left`, measured_ms 16450, steps_completed 1. A real tab close couldn't be automated (headless `page.close()` sends nothing), so navigating away mid-run was used instead. |
| 7 | Backend `mock`. The crisis phrase check only runs on typed text, and 3.2 has no typed input in the UI (the reframe is 3.3). Check it through the API in terminal 3: `curl -s -X POST localhost:8010/api/sessions -H 'Content-Type: application/json' -d '{"client_id":"manual-crisis","skill":"reframe"}' > /dev/null; curl -s -X POST localhost:8010/api/sessions/manual-crisis/messages -H 'Content-Type: application/json' -d '{"text":"Fictional test phrase: I want to die"}'` | Response: `"status":"scripted","crisis":true` with the scripted reply. Backend terminal shows no `model_client` log line for this request. | `sqlite3 backend/skills.db "SELECT role, text, model_status, crisis_flag FROM messages ORDER BY id DESC LIMIT 2;"` → user row with empty text and `crisis_flag=1`, then a scripted row with `crisis_flag=1` | Verified by automated run, see [final-checks.md](final-checks.md). `"status":"scripted","crisis":true`; user row with empty text and `crisis_flag=1`; scripted row with `crisis_flag=1`; no `model_client` log line. Run on port 8093. |
| 8 | Backend `mock`. Tap **Open practice**. At "Cycle 2 of 7" tap the **Crisis** tab, wait about 10 s, tap **Back to where I was**. Let it finish. | Circle, dots and caption freeze while the panel is open and continue from the same point. Console: `crisis_ms≈10000`, `measured_ms≈75000`. | `… sessions … LIMIT 1` → crisis_ms ≈ 10000, measured_ms ≈ 75000 | Verified by automated run, see [final-checks.md](final-checks.md). crisis_ms 10116, measured_ms 75018, completed; caption "Cycle 2 of 7" before, during, and after the panel. |
| 9 | After the runs above, tap the **History** tab (or the History card on Home). Tap **Show message** on one row. | One row per session: a coloured status dot with Completed / Stopped / Left, Paced breathing, date, and "Active … of 75.0 s planned" with how it ended. Message text only after the tap. No scores, no streaks. | `backend/.venv/bin/python backend/scripts/show_db.py` | |
| 10 | Tap the **Home** tab. | The featured card is labelled "Your usual", with a "Use my usual: Paced breathing" link under **Open practice** (derived from history: most recent Helped, otherwise most completed). Tapping it starts the intro directly; nothing starts by itself. | `curl -s localhost:8010/api/usual` → `{"skill":"breathing"}` | |

Extra, optional: in macOS System Settings → Accessibility → Display, turn on **Reduce motion**, reload, and run breathing. The **Animate circle** switch starts off, the circle stays still, and the "Breathe in" / "Breathe out" label carries the pace (no seconds countdown). The switch can turn the animation back on.
