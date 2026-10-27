# Restyle re-run (3.2-style branch)

The breathing app was restyled after the original 3.2 runs. The layout and colours were inspired by course demo screenshots (kept locally in `docs/reference/`, which is gitignored and never committed). **Behavior did not change.** These are the same browser checks as [browser-run.md](browser-run.md), run again on the new look.

Run on 2026-10-27, macOS, Playwright 1.49.1 driving headless Chromium 131. My own servers on free ports: backend 8041 with a scratch SQLite file and `LLM_MODE=mock`, frontend 5201, and a second frontend on 5202 proxied to port 8099, where nothing was listening, to simulate the backend being down. Ports 8000, 8010, 5173 and 5180 were not touched, and `backend/skills.db` was never opened. Fictional data only.

Script: [restyle/restyle-run.mjs](restyle/restyle-run.mjs). Screenshots: [restyle/](restyle/) (`01`–`11`). Wall-clock time 98 s.

| Check | Console `[timing]` / result | DB row | Outcome |
|---|---|---|---|
| Full run | `measured_ms=75009 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed`, `setup_ms=203` | session 2: completed, 7/7 | Closing "You came in feeling tense and took seven slow breaths." (mock). Check-in "Helped" saved |
| Pause 3 s, then Crisis tab for 5 s | `measured_ms=75016 pauses_ms=3048 crisis_ms=5083 planned_ms=75000 end_reason=completed` | session 1: completed, pauses 3048, crisis 5083 | "Cycle 2 of 7" before opening the panel and "Cycle 2 of 7" after closing it: resumed at the same point (`06`) |
| Backend down | `measured_ms=75012 … end_reason=completed`; `[session] write failed … HTTP 500`; `[model] acknowledgment unavailable: showing fixed fallback` | none (backend unreachable) | Crisis tab opened from Home (`07`); breathing ran to the end with "That was seven slow breaths." (`08`) |
| Stop exercise after ~13 s | `measured_ms=13386 … end_reason=stopped` | session 3: stopped, 0/7 | "Stopped. That's fine." (`09`), no check-in |
| Tab bar | During the exercise: `["Crisis"]`. After it: `["Home", "History", "Crisis"]` | n/a | Contracts to Crisis only while breathing runs (D1) |
| Home and History after the runs | n/a | n/a | "Use my usual: Paced breathing" (`10`). History chips Stopped, Completed, Completed (`11`) |

The first attempt of this script failed at the stop run. It waited for an "Open practice" button, but by then Home correctly showed "Use my usual: Paced breathing", because the earlier run had been rated Helped. That was a script bug, not an app bug. The script now taps the featured card's button whatever its label, and the numbers above come from the rerun on a fresh scratch database.

## Database after the run

$ cd backend && .venv/bin/python scripts/show_db.py <scratch db>

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 114f7710-6304-4dd9-94e4-31e0da87252b | breathing |  | completed | 1 | 0 | 80 | 75000 | 75016 | 3048 | 5083 | 7 | 7 | 2026-10-27T17:59:20.004Z | 2026-10-27T18:00:43.161+00:00 |
| 2 | 395201e8-f815-4bb5-a92e-361b4435a614 | breathing | tense | completed | 1 | 0 | 203 | 75000 | 75009 | 0 | 0 | 7 | 7 | 2026-10-27T17:59:20.124Z | 2026-10-27T18:00:35.142+00:00 |
| 3 | 8508fccb-6c5a-42e3-b80c-abe39e25f6d5 | breathing |  | stopped | 0 | 1 | 45 | 75000 | 13386 | 0 | 0 | 7 | 0 | 2026-10-27T18:00:43.503Z | 2026-10-27T18:00:56.897+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 2 | model | You came in feeling tense and took seven slow breaths. | mock | 1 | 0 | 2026-10-27T18:00:25.151+00:00 |
| 2 | 1 | model | You took seven slow breaths. | mock | 0 | 0 | 2026-10-27T18:00:33.161+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|
| 1 | 2 | helped |
