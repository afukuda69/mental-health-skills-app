# Screencast plan

Two recordings, or one with clearly marked sections. Use fictional scenarios only. Say out loud that this is a coursework prototype.

## Before recording

```bash
# Terminal 1
cd backend
rm -f /tmp/skills-demo.db
SKILLS_DB_PATH=/tmp/skills-demo.db .venv/bin/python scripts/seed_demo.py
SKILLS_DB_PATH=/tmp/skills-demo.db LLM_MODE=mock .venv/bin/uvicorn main:app --port 8000

# Terminal 2
cd frontend
npm run dev        # http://localhost:5173
```

If 8000 or 5173 is taken, use the README's alternate ports. Set the browser to about 1280 px wide. Use mock mode so the demo can't stall on the free model.

## Part 1: demo of the finished app (5 minutes at most)

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | Home | What it is: a coursework skills prototype, three short skills. Not a support service. Nobody monitors it. Nothing starts by itself (R4). |
| 0:25–1:05 | Tap **Tense or wound up**, then **Change**, then **Overwhelmed**, then **Show everything** | The check-in changes what is suggested. Overwhelmed contracts Home to one button and Crisis (D1). The app can't detect distress, so the user's own tap is the only signal, and one tap undoes it. |
| 1:05–2:10 | From Activities, **Start Paced breathing**. Tap **Start**. After a few breaths tap **Crisis**, wait, tap **Back to where I was**, then **Stop exercise** | The circle carries the pace, with no countdown (D6). Only Crisis stays in the bar (D1, D4). Crisis pauses the timer and returns to the same cycle. Stop is one tap, no dialog, no guilt (R3). |
| 2:10–2:50 | **STOP**: step through, open the optional note on Observe | One step per screen (D2). The note is hidden by default, and nothing typed is saved or sent (D3). |
| 2:50–3:30 | **Cognitive reframe**: tap a chip, type a fictional line, reach the reflection | Typing is optional. Only the step-3 answer goes to the model, and it is never stored. |
| 3:30–4:15 | **Chat**: send "Fictional: nervous before a presentation, any help?", then "Can you tell me if I have anxiety?" | The limits bar. The model offers, and the user taps. A diagnosis request gets the limit reply. Be honest: this is mock mode, and the live model did not use the name (docs/evaluation.md). |
| 4:15–4:50 | **Profile**: usual skill and its source, change it, **Reset to learned**, then History | Learned by default, correctable (D5, R4). Each item shows where it came from. |
| 4:50–5:00 | End on Crisis | Available everywhere, and independent of the model and the backend. |

Optional if time allows: stop the backend in Terminal 1 and open Crisis to show that it still works.

## Part 2: process screencast, one failure (about 4 minutes)

**The failure:** the OpenRouter keep-alive timeout. The app's 5 s limit stopped waiting, but it did not stop the work.

| Time | Show | Say |
|---|---|---|
| 0:00–0:40 | [docs/evidence/3.2/api-checks.md](../3.2/api-checks.md), the two `LLM_MODE=live` lines with `status: timeout` and latency about 5009 ms. Then [live-latency-run1.txt](../3.2/live-latency-run1.txt) with its 3.8 s median | **The failure.** Both live calls through the server timed out, while direct calls were usually fast. My first guess was that the server path was slower. |
| 0:40–1:40 | The log excerpt in [server-path-diagnosis.md](../3.2/server-path-diagnosis.md), Step 1: `200 OK` appears **before** the timeout warning | **Evidence 1.** httpx logs that line when the headers arrive, so the server answered early and the body was what took long. |
| 1:40–2:30 | Step 2 of the same file: queue delay 0 ms; `first_bytes: b'\n         \n'`; true call time 12.6 s; and call 8 in run 1, 45.9 s with a 30 s timeout | **Evidence 2.** I compared both paths in one process. No difference, so the two timeouts were variance. But OpenRouter sends keep-alive whitespace, which resets httpx's read timeout, so that timeout never fired and abandoned calls kept running. |
| 2:30–3:30 | Open [backend/model_client.py](../../../backend/model_client.py) at **`_call_openrouter`, lines 161–183**. Point to line 166 (`deadline`), lines 177–180 (the loop that checks it for every chunk), and line 180 (`LLMDeadlineError`). Then `_run_in_thread`, **lines 96–108**, and `_invoke`, **line 227** (`future.result(timeout=TIMEOUT_S)`) | **Generated code explained.** httpx's `timeout` limits each read, not the whole request. So the code reads the response as a stream and checks a wall-clock deadline on every chunk, then stops. `future.result` is what the user waits on. Each call has its own thread, so an abandoned call can't delay the next one. |
| 3:30–4:00 | `test_call_is_abandoned_at_the_deadline_despite_keepalive_bytes` and `test_abandoned_slow_calls_do_not_delay_the_next_call` in [backend/tests/test_model_client.py](../../../backend/tests/test_model_client.py) (lines 152 and 163) | **The decision.** Enforce the time limit in the app, not through the HTTP client. Turn reasoning off, since about 85% of output was reasoning. The first test fakes the keep-alive bytes, and the second failed on the old pooled code. |

To show the old code, run `git show 774896b:backend/model_client.py` and look at `_call_openrouter`, which used `httpx.post(..., timeout=TIMEOUT_S)`. The fix is commit `b83a946`.
