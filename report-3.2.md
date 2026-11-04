# Assignment 3.2 — Working Application and Safety: Submission

- **Repository:** `https://github.com/afukuda69/mental-health-skills-app`
- **Commit:** `SUBMITTED_COMMIT_SHA`

## Documents and evidence

- [README.md](README.md): setup from a clean checkout (bash, plus PowerShell), settings, tests, mock/live switch
- [docs/design.md](docs/design.md): design, updated open questions (§k), and **Changes since 3.1** with the measured duration (§l)
- [docs/evidence-log.md](docs/evidence-log.md): prompts → changes → observations → decisions, including bugs and failed approaches
- [AI-USE.md](AI-USE.md): Claude Code version and the app's runtime model
- Evidence in [docs/evidence/3.2/](docs/evidence/3.2/):
  - [pytest-output.txt](docs/evidence/3.2/pytest-output.txt), [vitest-output.txt](docs/evidence/3.2/vitest-output.txt), [build-output.txt](docs/evidence/3.2/build-output.txt)
  - [final-checks.md](docs/evidence/3.2/final-checks.md) and [final/](docs/evidence/3.2/final/): automated runs for checklist rows 2b, 4a, 4b, 6, 7 and 8, on the current look
  - [api-checks.md](docs/evidence/3.2/api-checks.md): every endpoint in every `LLM_MODE`, with the resulting database rows
  - [restyle-run.md](docs/evidence/3.2/restyle-run.md) and [restyle/](docs/evidence/3.2/restyle/): the same browser checks re-run on the **current look**, with screenshots
  - [browser-run.md](docs/evidence/3.2/browser-run.md) and [browser/](docs/evidence/3.2/browser/): the original headless Chromium runs. Their screenshots show the earlier look; behavior is the same
  - [live-latency-run1.txt](docs/evidence/3.2/live-latency-run1.txt), [live-latency-run2.txt](docs/evidence/3.2/live-latency-run2.txt): live model latency and outputs
  - [server-path-diagnosis.md](docs/evidence/3.2/server-path-diagnosis.md): why live server calls timed out, the fixes, and a model comparison
  - [port-conflict.txt](docs/evidence/3.2/port-conflict.txt), [vitest-first-failure.txt](docs/evidence/3.2/vitest-first-failure.txt): failures and their fixes
  - [manual-checks.md](docs/evidence/3.2/manual-checks.md): browser checklist with expected results and an Observed column
  - [Screen recording](https://drive.google.com/file/d/129JPv1-0rBF0R__5kqGLcC7qO--4IEpB/view?usp=sharing): shows the **earlier look**. The current look is shown by [restyle-run.md](docs/evidence/3.2/restyle-run.md), which re-ran the same checks with no behavior change

## What is complete

- **Paced breathing end to end** through the running interface: Home (optional "How are you right now?" choice, then Open practice or Use my usual), intro, 7 × (4 s in / 6 s out) with "Breathe in" / "Breathe out" and "Cycle n of 7", closing acknowledgment, check-in, Done. Pause and Resume. An "Animate circle" switch, which starts from the system's reduce-motion setting; with it off, the circle stays still and the label carries the pace (no seconds countdown).
- **Model contribution** as designed: one short closing acknowledgment from the entry choice and a count of earlier sessions. It is requested at the start of cycle 7 and never blocks the timer. Output is checked in code (≤ 30 words, no `?`/`!`, banned words, must end with a full stop), with a 5 s wall-clock limit (the response is abandoned at the deadline) and fixed fallback text. Model reasoning is off by default.
- **Persistence in SQLite:** `sessions` (timing, end reason, entry choice, steps), `messages` (the conversation record: model, fallback, scripted, and user rows, with `model_status`, `latency_ms`, `crisis_flag`), and `feedback`. History and "Use my usual" read from it.
- **Crisis route independent of the backend, model, and any classifier:** a Crisis tab in the bottom bar on every screen, the only tab while the exercise runs, opening a static panel. Verified with the backend down.
- **Supplementary phrase check** before any model call (one shared list): scripted reply, no model call, crisis flag stored without the text. Verified by tests and the API. There is no typed input in breathing, so the browser version comes with the 3.3 reframe.
- **Exits:** Stop exercise (one tap, no dialog) → `stopped` → "Stopped. That's fine."; leaving the page → `left` via `sendBeacon`; returning to a hidden tab finds the exercise paused.
- **Mock and failure modes:** `mock`, `mock_error`, `mock_timeout`, `mock_malformed`, `live`, and an `LLM_MAX_CALLS` cap (default 50) that switches to mock.
- **Tests:** 64 backend (pytest) and 23 frontend (vitest), all mocked with network blocked. A deliberate mutation check showed the suite catches a broken crisis matcher and a broken end-reason guard.

## Measured exercise duration

| Measure | Value | Source |
|---|---|---|
| Planned (intro 5 s + 7 × 10 s) | 75 000 ms | `frontend/src/timing.js`, test in vitest |
| Measured, automated, intro left to run | **75 012 ms** on the current look; 75 001–75 018 ms across the four final full runs, including the live one | headless Chromium, [restyle-run.md](docs/evidence/3.2/restyle-run.md), [final-checks.md](docs/evidence/3.2/final-checks.md) |
| Measured, with a 3 s pause and 5 s in the crisis panel | 75 004 ms (`pauses_ms` 3 033, `crisis_ms` 5 081, stored separately) | [restyle-run.md](docs/evidence/3.2/restyle-run.md) |
| Measured, with 10 s in the crisis panel | 75 018 ms (`crisis_ms` 10 116, stored separately) | [final-checks.md](docs/evidence/3.2/final-checks.md) |
| Measured, my own runs in a real browser | **71 124 ms and 71 084 ms** (sessions 3 and 4), 7/7 cycles each | `backend/skills.db`, [manual-checks.md](docs/evidence/3.2/manual-checks.md) row 1 |
| Entry and skill pick (reported separately) | `setup_ms` 20 137 and 27 958 ms in those two runs; under 400 ms in scripted runs | same sources |

**Assumptions:**
- The measure runs from the first exercise instruction (the intro text) to the final planned step (closing text on screen), counting active time only. User pauses, hidden-tab time, and crisis-panel time are excluded and stored separately.
- The clock starts when the intro text appears, not when "Start" is tapped. The intro advances by itself after 5 s, or earlier if the user taps "Start".
- With the mock, app delay is about 10 ms. With a live model the request starts 10 s before the closing step, and the backend limit is 5 s, so the closing text is never late. Worst case stays at 75 s plus frame timing, within the 90 s limit.

**Why my two real-browser runs measured 71 s, not 75 s:** tapping "Start" ends the 5 s intro early, and nothing else is shortened.

- **In the code:** `startNow()` in `BreathingSkill.vue` sets the end of the intro to the moment of the tap. Without a tap, it is set at 5 000 ms. The seven 10 s cycles then always run in full from that point, so measured time = time spent on the intro + 70 000 ms + any closing delay.
- **In the data:** 71 124 ms and 71 084 ms mean about 1.1 s was spent on the intro, so about 3.9 s of it was skipped. The acknowledgment request is sent at the start of cycle 7, which is 60 s after the intro ends. Its rows were saved 61.14 s and 61.09 s after those sessions started, which also gives an intro of about 1.1 s. A later run (session 22) fits the same pattern: 71 317 ms, with the row saved at 61.35 s.
- **How the definition handles it:** the definition is first exercise instruction to final planned step, in active time. The intro text is the first instruction, so the clock starts there either way and `measured_ms` records what really happened. A shorter intro is a shorter measured time, not an error or a skipped step: both sessions show `steps_completed` 7 of 7. `planned_ms` stays 75 000 because it assumes the full intro. Every run is within the 90 s limit.

## What the evidence shows

- The breathing exercise runs in the browser in 75.0 s and writes a matching database row (`measured_ms` equal to the console `[timing]` line).
- Every model failure mode shows "That was seven slow breaths." and stores a `fallback` row with the right `model_status` (`error`, `timeout`, `fallback`). The exercise and the crisis route carry on.
- **Live model** (`nvidia/nemotron-3-ultra-550b-a55b:free`):
  - **Latency:** before the fixes below, 10 of 17 raw calls finished within 5 s (median 3.5 s, max 45.9 s), and both live calls made through the running server timed out.
  - **Final live run:** one full browser run on the current code returned model text in 731 ms (`status=ok`) ([final-checks.md](docs/evidence/3.2/final-checks.md)).
  - **Accepted replies:** they restate the fallback plus the entry choice and the session count.
  - **Rejected reply:** one call leaked the model's reasoning, and the check rejected it.
  - **Bug found:** one reply was cut off mid-sentence and passed the 3.1 checks. It is now rejected (commit `774896b`).
  - **Server-path timeouts:** the server path is not slower than a direct call (same payload, 0 ms queue delay). The 2 timeouts were latency variance. Three fixes came out of the diagnosis: abandon the stream at the deadline (OpenRouter's keep-alive bytes defeat httpx's read timeout), run each call on its own thread (a shared pool could queue calls behind abandoned ones), and turn reasoning off. After the fix the same model answered in 1.9–2.8 s through the server ([server-path-diagnosis.md](docs/evidence/3.2/server-path-diagnosis.md)).
- **Backend stopped:** the crisis panel opens, breathing completes, and failed writes only log console warnings.
- **Leaving:** Stop exercise records `stopped`, and navigating away records `left`. The crisis panel pauses the exercise, which resumes at the same cycle: 10 s in the panel gave `crisis_ms` 10 116 and left `measured_ms` at 75 018.

## Unfinished / known limitations

- **STOP and the reframe** are deferred to Part 3.3. The registry and the step frame are ready for them.
- **Crisis phrase list:** it misses misspellings, indirect phrasing, and other languages, and it gives false positives on idioms. It is a supplement, not a safety mechanism. In 3.2 it can only be exercised through the API, because breathing has no typed input.
- **Tab close** sends `left` with `sendBeacon` on `pagehide`/`visibilitychange`. This was verified for navigating away, but **not for a real tab close**: headless `page.close()` sent nothing, so checklist row 6 used navigation away instead, and my own database has no `left` row. If the browser drops the beacon, the session stays without an end reason and shows as "Not finished" in History.
- **Manual checks:** rows 1, 2a, 3 and 5 of [manual-checks.md](docs/evidence/3.2/manual-checks.md) come from my own runs and the [screen recording](https://drive.google.com/file/d/129JPv1-0rBF0R__5kqGLcC7qO--4IEpB/view?usp=sharing), which shows the earlier look. Rows 2b, 4a, 4b, 6, 7 and 8 were run automatically, not by hand. Rows 9 and 10 have no Observed entry; [restyle-run.md](docs/evidence/3.2/restyle-run.md) covers History and "Use my usual" automatically.
- **Live model:** before the reasoning fix, about 40% of acknowledgments fell back because of latency. After it, the few calls made (n = 3 on the current model) took 0.7–2.8 s, which is not yet a reliable rate. The key is free tier: free models can be rate-limited (one returned 429), and the app falls back. Whether the model adds anything over the fallback (open question 5) needs peer testing.
- **Platform:** tested on macOS only (Chromium headless, Python 3.14, Node 24). The Windows PowerShell commands in the README are untested.
- **Crisis resources** are US-only.
- **Live call cap:** `LLM_MAX_CALLS` counts per server process and resets on restart.
