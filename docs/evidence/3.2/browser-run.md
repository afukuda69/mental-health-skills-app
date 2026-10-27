# Automated browser run (headless Chromium)

Run on 2026-10-27 on macOS with Playwright 1.49.1 driving headless Chromium 131 against the real Vite dev server and FastAPI backend. Backend in `LLM_MODE=mock`, temporary SQLite file. Fictional data only.

- Script: [browser/browser-run.mjs](browser/browser-run.mjs). Not part of the app or the test suite.
- Ports: backend 8010, frontend 5180. A second frontend on 5181 proxied to an unused port to simulate the backend being down.
- Screenshots: [browser/](browser/) (`01`–`10`).
- Total wall-clock time for all runs: 111 s. Three 75 s runs ran in parallel.

These runs are automated. The manual checklist ([manual-checks.md](manual-checks.md)) repeats them in a real browser with screenshots, and covers what automation could not: a real tab close, and a live model run.

## Results

| Run | Console `[timing]` line | DB row (`sessions`) | Result |
|---|---|---|---|
| Clean full run | `measured_ms=75010 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed`, `setup_ms=188` | id 1: completed, measured 75010, steps 7/7 | Closing text "You came in feeling tense and took seven slow breaths." (mock). Check-in "Helped" saved. |
| Pause 3 s + crisis panel 5 s mid-run | `measured_ms=75007 pauses_ms=3034 crisis_ms=5082 planned_ms=75000 end_reason=completed` | id 2: completed, measured 75007, pauses 3034, crisis 5082 | Counter read "2 of 7" before opening the panel and "2 of 7" after closing it: the exercise resumed at the same point. |
| Backend down | `measured_ms=75013 … end_reason=completed`, plus `[session] write failed … HTTP 500` and `[model] acknowledgment unavailable: showing fixed fallback` | none (backend unreachable) | Crisis panel opened from entry (`06`). Breathing ran to the end, and the closing showed the fallback "That was seven slow breaths." (`07`). No "Use my usual" button, because history couldn't be read. |
| Stop exercise after ~13 s | `measured_ms=13377 … end_reason=stopped` | id 3: stopped, exited_early 1, steps 0/7 | "Stopped. That's fine." (`08`). No check-in. |
| Close tab mid-run (`page.close()`) | n/a | id 4: no end recorded | **Not verified.** See below. |
| Navigate away mid-run | n/a | id 5: left, measured 6142 | Recorded through `visibilitychange`/`pagehide` + `sendBeacon`. |
| Entry after the runs | n/a | n/a | "Use my usual: Paced breathing" (`09`). History lists Finished / Stopped early / Not finished, and the acknowledgment text appears only after "Show message" (`10`). |

Measured duration of the clean run: **75.01 s** from the first instruction (the intro text) to the closing text on screen, against a plan of 75.00 s. App delay was about 10 ms, because the mock acknowledgment was requested at the start of cycle 7 and was back long before the closing step. Entry and skill pick (`setup_ms`) are reported separately. They are tiny here because a script clicked the buttons.

## Tab close: what failed and how it was diagnosed

The first run closed the page with Playwright's `page.close({ runBeforeUnload: true })`. The session stayed open (id 4, history "Not finished"), and the backend log showed no `/end` request.

Diagnosis ([browser/beacon-diagnosis.mjs](browser/beacon-diagnosis.mjs)), with the backend request log:

| Step | Request reached backend |
|---|---|
| Direct `navigator.sendBeacon('/api/sessions/diag-none/end', …)` through the Vite proxy | yes (404, expected for an unknown id) |
| Navigate the page to `about:blank` mid-run | yes, twice (visibilitychange and pagehide both fire; the second write changes nothing) |
| `page.close({ runBeforeUnload: true })` | no |
| `page.close()` | no |

So the beacon and the proxy work, and leaving by navigation is recorded. Headless `page.close()` sends nothing, so a real tab close can't be verified this way. Manual check 6 covers it in a real browser.
