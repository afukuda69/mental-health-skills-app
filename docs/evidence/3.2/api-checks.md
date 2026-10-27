# Endpoint checks against a running backend

Run on 2026-10-27, macOS, backend on port 8010 (8000 was taken by another local app, see port-conflict.txt), temporary SQLite file. Each mode is a fresh server start with that LLM_MODE. Fictional data only.

Script: [backend/scripts/api_checks.sh](../../../backend/scripts/api_checks.sh). Note: the `measured_ms` values here are typed into the request by the script; real browser measurements are in [browser-run.md](browser-run.md).

```text
### LLM_MODE=mock
## GET /api/health
{"status":"ok"}
## Completed run: start, acknowledgment, end, feedback
-> acknowledgment:
{"text":"You came in feeling tense and took seven slow breaths.","status":"mock","latency_ms":0,"crisis":false}
-> end completed:
{"id":1,"client_id":"demo-complete","skill":"breathing","entry_choice":"tense","started_at":"2026-10-27T15:47:05.219+00:00","ended_at":"2026-10-27T15:47:05.239+00:00","completed":1,"exited_early":0,"e
-> feedback:
{"saved":true}
## Stop exercise mid-run, then an acknowledgment request (must be refused, no model call)
{"id":2,"client_id":"demo-stopped","skill":"breathing","entry_choice":"tense","started_at":"2026-10-27T15:47:05.256+00:00","ended_at":"2026-10-27T15:47:05.264+00:00","completed":0,"exited_early":1,"en
acknowledgment after stop -> HTTP 409
## Left the page: sendBeacon-style text/plain body
{"id":3,"client_id":"demo-left","skill":"breathing","entry_choice":"tense","started_at":"2026-10-27T15:47:05.279+00:00","ended_at":"2026-10-27T15:47:05.287+00:00","completed":0,"exited_early":1,"end_r

## Crisis phrase in typed text (fictional): scripted reply, no model call
{"text":"Crisis support is open. It lists people you can call or text right now.","status":"scripted","latency_ms":null,"crisis":true}
## Ordinary typed text (fictional): stored, model reply
{"text":"Another way to see it: it may not be as certain as it feels.","status":"mock","latency_ms":0,"crisis":false}
## GET /api/usual
{"skill":"breathing"}
### LLM_MODE=mock_error
{"text":"That was seven slow breaths.","status":"error","latency_ms":0,"crisis":false}
### LLM_MODE=mock_timeout
{"text":"That was seven slow breaths.","status":"timeout","latency_ms":5005,"crisis":false}
### LLM_MODE=mock_malformed
{"text":"That was seven slow breaths.","status":"fallback","latency_ms":0,"crisis":false}
### LLM_MODE=live
{"text":"That was seven slow breaths.","status":"timeout","latency_ms":5009,"crisis":false}
### LLM_MODE=live
{"text":"That was seven slow breaths.","status":"timeout","latency_ms":5010,"crisis":false}
```

Server log lines from model_client:

```text
INFO model_client: model output rejected by check_output (mode=mock_malformed)
WARNING model_client: model call failed (mode=mock_error): LLMRequestError
WARNING model_client: model call timed out after 5.0 s (mode=live)
WARNING model_client: model call timed out after 5.0 s (mode=mock_timeout)
```

Note: both live calls went to the same session (script reused its random id; session create is idempotent). Both hit the 5 s wall-clock limit and stored the fallback with model_status=timeout.

## Database after the checks

$ cd backend && .venv/bin/python scripts/show_db.py <temp db>

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | demo-complete | breathing | tense | completed | 1 | 0 | 6400 | 75000 | 75412 | 0 | 0 | 7 | 7 | 2026-10-27T15:47:05.219+00:00 | 2026-10-27T15:47:05.239+00:00 |
| 2 | demo-stopped | breathing | tense | stopped | 0 | 1 | 6400 | 75000 | 23110 | 0 | 0 | 7 | 1 | 2026-10-27T15:47:05.256+00:00 | 2026-10-27T15:47:05.264+00:00 |
| 3 | demo-left | breathing | tense | left | 0 | 1 | 6400 | 75000 | 31877 | 0 | 0 | 7 | 2 | 2026-10-27T15:47:05.279+00:00 | 2026-10-27T15:47:05.287+00:00 |
| 4 | demo-crisis | reframe | okay |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:05.295+00:00 |  |
| 5 | demo-text | reframe | okay |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:05.311+00:00 |  |
| 6 | demo-mock_error-28804 | breathing | tense |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:08.896+00:00 |  |
| 7 | demo-mock_timeout-28804 | breathing | tense |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:12.490+00:00 |  |
| 8 | demo-mock_malformed-28804 | breathing | tense |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:21.140+00:00 |  |
| 9 | demo-live-28804 | breathing | tense |  | 0 | 0 | 6400 | 75000 |  |  |  | 7 |  | 2026-10-27T15:47:24.743+00:00 |  |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 1 | model | You came in feeling tense and took seven slow breaths. | mock | 0 | 0 | 2026-10-27T15:47:05.230+00:00 |
| 2 | 4 | user |  |  |  | 1 | 2026-10-27T15:47:05.303+00:00 |
| 3 | 4 | scripted | Crisis support is open. It lists people you can call or text right now. | scripted |  | 1 | 2026-10-27T15:47:05.304+00:00 |
| 4 | 5 | user | Fictional: the presentation might go fine |  |  | 0 | 2026-10-27T15:47:05.319+00:00 |
| 5 | 5 | model | Another way to see it: it may not be as certain as it feels. | mock | 0 | 0 | 2026-10-27T15:47:05.320+00:00 |
| 6 | 6 | fallback | That was seven slow breaths. | error | 0 | 0 | 2026-10-27T15:47:08.908+00:00 |
| 7 | 7 | fallback | That was seven slow breaths. | timeout | 5005 | 0 | 2026-10-27T15:47:17.509+00:00 |
| 8 | 8 | fallback | That was seven slow breaths. | fallback | 0 | 0 | 2026-10-27T15:47:21.154+00:00 |
| 9 | 9 | fallback | That was seven slow breaths. | timeout | 5009 | 0 | 2026-10-27T15:47:29.766+00:00 |
| 10 | 9 | fallback | That was seven slow breaths. | timeout | 5010 | 0 | 2026-10-27T15:47:38.402+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|
| 1 | 1 | helped |
