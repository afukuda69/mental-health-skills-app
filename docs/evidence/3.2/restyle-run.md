# Restyle re-run (3.2-style branch)

The breathing app's look was **inspired by the course demo, then changed to a baby-blue palette and a different layout to keep the design my own.** The demo screenshots are kept locally in `docs/reference/`, which is gitignored and never committed. **Behavior did not change.** These are the same browser checks as [browser-run.md](browser-run.md), run again on the current look.

Run on 2026-10-27, macOS, Playwright 1.49.1 driving headless Chromium 131. My own servers on free ports: backend 8051 with a scratch SQLite file and `LLM_MODE=mock`, frontend 5211, and a second frontend on 5212 proxied to port 8098, where nothing was listening, to simulate the backend being down. Other ports in use were not touched: 8000, 8010, 5173, 5180, and 8041, which another server had already taken. `backend/skills.db` was never opened. Fictional data only.

Script: [restyle/restyle-run.mjs](restyle/restyle-run.mjs). Screenshots: [restyle/](restyle/) (`01`–`11`). Wall-clock time 98 s.

| Check | Console `[timing]` / result | DB row | Outcome |
|---|---|---|---|
| Full run | `measured_ms=75012 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed`, `setup_ms=373` | session 2: completed, 7/7 | Closing "You came in feeling tense and took seven slow breaths." (mock). Check-in "Helped" saved |
| Pause 3 s, then Crisis tab for 5 s | `measured_ms=75004 pauses_ms=3033 crisis_ms=5081 planned_ms=75000 end_reason=completed` | session 1: completed, pauses 3033, crisis 5081 | Caption "Cycle 2 of 7" before opening the panel and after closing it: resumed at the same point (`06`) |
| Backend down | `measured_ms=75011 … end_reason=completed`; `[session] write failed … HTTP 500`; `[model] acknowledgment unavailable: showing fixed fallback` | none (backend unreachable) | Crisis tab opened from Home (`07`); breathing ran to the end with "That was seven slow breaths." (`08`) |
| Stop exercise after ~13 s | `measured_ms=13403 … end_reason=stopped` | session 3: stopped, 0/7 | "Stopped. That's fine." (`09`), no check-in |
| Tab bar | During the exercise: `["Crisis"]`. After it: `["Home", "History", "Crisis"]` | n/a | Contracts to Crisis only while breathing runs (D1) |
| Home and History after the runs | n/a | n/a | "Use my usual: Paced breathing" link under Open practice (`10`). History status: Stopped, Completed, Completed (`11`) |

Notes on this run:
- An earlier run of this script, on the first restyle, failed at the stop run. It waited for an "Open practice" button, but Home correctly showed "Use my usual" after a run rated Helped. That was a script bug, and the script now taps the featured card's primary button.
- For this re-run, the selectors moved to the new cycle caption and history rows.
- Port 8041 was busy with a server I hadn't started, so I moved to 8051/5211/5212.

## Database after the run

$ cd backend && .venv/bin/python scripts/show_db.py <scratch db>

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 790ec152-791f-40bf-acb6-3da81e40123b | breathing |  | completed | 1 | 0 | 65 | 75000 | 75004 | 3033 | 5081 | 7 | 7 | 2026-10-27T18:15:34.295Z | 2026-10-27T18:16:57.429+00:00 |
| 2 | ff71295a-1c5f-47ec-9d10-085dfd38cd70 | breathing | tense | completed | 1 | 0 | 373 | 75000 | 75012 | 0 | 0 | 7 | 7 | 2026-10-27T18:15:34.603Z | 2026-10-27T18:16:49.627+00:00 |
| 3 | a829d343-1ecd-4043-8766-66951fe79d26 | breathing |  | stopped | 0 | 1 | 53 | 75000 | 13403 | 0 | 0 | 7 | 0 | 2026-10-27T18:16:57.801Z | 2026-10-27T18:17:11.214+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 2 | model | You came in feeling tense and took seven slow breaths. | mock | 1 | 0 | 2026-10-27T18:16:39.632+00:00 |
| 2 | 1 | model | You took seven slow breaths. | mock | 1 | 0 | 2026-10-27T18:16:47.428+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|
| 1 | 2 | helped |
