# Why live calls through the server timed out (2026-10-27, macOS)

**Question:** in [api-checks.md](api-checks.md), both live acknowledgments through the running server timed out at 5 s, while direct calls in [live-latency-run1.txt](live-latency-run1.txt) had a 3.5 s median. Is the server path slower?

**Short answer:** no. The server path and the direct path behave the same. The two timeouts were the model's latency variance (about 40% of calls took over 5 s on either path). The investigation did find three real problems, now fixed:

1. The 5 s limit stopped waiting but didn't stop the HTTP call.
2. A shared pool of 4 threads could queue new calls behind abandoned ones.
3. Most of the model's output was reasoning tokens.

Live calls used: 10 (4 for the diagnosis, 6 for the model comparison).

## Step 1: read the server log from the failed run

```text
INFO httpx: HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
WARNING model_client: model call timed out after 5.0 s (mode=live)
```

httpx logs that line when the **headers** arrive. They arrived before the 5 s deadline; the body did not.

## Step 2: compare the two paths in one process (4 live calls)

Script: [backend/scripts/diag_server_path.py](../../../backend/scripts/diag_server_path.py). It runs the real app in-process, wraps the model call to record queue delay and true completion time, and alternates with a direct streamed request that uses the same payload.

```text
model: nvidia/nemotron-3-ultra-550b-a55b:free  app timeout: 5.0 s

server #1: {'endpoint_ms': 5014, 'status': 'timeout', 'app_latency_ms': 5005}
direct #1: {'first_bytes': b'\n         \n', 'headers_ms': 350, 'http_status': 200, 'first_byte_ms': 511, 'total_ms': 4514, 'leading_whitespace_bytes': 22, 'reasoning_tokens': 85, 'completion_tokens': 88, 'reply': 'You completed seven paced breaths after starting out feeling tense.'}
server #2: {'endpoint_ms': 2017, 'status': 'ok', 'app_latency_ms': 2001}
direct #2: {'first_bytes': b'\n         \n', 'headers_ms': 424, 'http_status': 200, 'first_byte_ms': 600, 'total_ms': 5134, 'leading_whitespace_bytes': 22, 'reasoning_tokens': 75, 'completion_tokens': 92, 'reply': 'You completed seven paced breaths, starting from a tense state. This was your first breathing session.'}

server-path model calls (true timing, measured inside the worker thread):
  #1: queue_delay_ms=0 call_ms=12551 outcome=reply reply='You completed seven paced breaths after starting out feeling tense.'
  #2: queue_delay_ms=0 call_ms=2001 outcome=reply reply='You completed seven paced breaths after starting out feeling tense.'
```

What this shows:

| Suspect | Finding |
|---|---|
| Event-loop blocking | No. The acknowledgment route is a sync `def`, which FastAPI runs in its thread pool. Queue delay before the model call was 0 ms. (Separately, the async `/end` route did its sqlite write on the event loop. It now uses `run_in_threadpool`.) |
| Payload | Same messages, model, `temperature`, and `max_tokens` on both paths (the direct leg builds them with `model_client.build_messages`). |
| Client setup | Both use a new `httpx` connection per call. Headers arrived in 350–424 ms on the direct path. |
| Timeout config | **Real issue.** OpenRouter sends headers right away, then whitespace keep-alive bytes (`first_bytes: b'\n         \n'` at about 0.5 s) while the model generates. httpx's timeout limits each read, so it never fires. The app's wall-clock limit returned the fallback at 5 s, but the worker thread kept going: server call #1 finished **12.6 s** later. |
| Server-only failure mode | **Latent issue.** Calls ran on a shared pool of 4 worker threads. Abandoned calls that keep running (up to 45.9 s seen) can hold every worker, so a new call waits in line, and the wait counts against its 5 s. Fresh test servers never hit this, but a long-running server would. Reproduced with mocks: `test_abandoned_slow_calls_do_not_delay_the_next_call` fails on the old code (the 6th call times out although its reply is instant) and passes after the fix. |
| Model output | **Real issue.** 75–85 of about 90 completion tokens were reasoning, which is latency for a one-sentence reply. |

## Step 3: fixes (no live calls; 64/64 tests pass)

- `model_client._call_openrouter` streams the response and abandons it at the wall-clock deadline (`LLMDeadlineError` → status `timeout`). Test: `test_call_is_abandoned_at_the_deadline_despite_keepalive_bytes`.
- Each call runs on its own daemon thread instead of the shared pool. Test: `test_abandoned_slow_calls_do_not_delay_the_next_call`.
- The payload sends `"reasoning": {"enabled": false}` unless `LLM_REASONING=on`. Test: `test_reasoning_off_by_default_and_configurable`.
- `/end` runs its database write in the thread pool.

## Step 4: compare free models with reasoning off (6 live calls)

The key is on OpenRouter's free tier with no credits (`GET /api/v1/key`: `is_free_tier: true`), so paid models such as `openai/gpt-4.1-nano` would be refused. Every free text model in the catalog supports reasoning.

Script: [backend/scripts/compare_models.py](../../../backend/scripts/compare_models.py).

```text
reasoning: off  app timeout: 5.0 s

## nvidia/nemotron-3-ultra-550b-a55b:free
- server path: endpoint 2754 ms, status=ok, shown: 'You completed seven slow breaths after starting out feeling overwhelmed.'
- raw (30 s limit): 1934 ms, completion_tokens=12, reasoning_tokens=0, passes check=True, reply: 'You completed seven slow breaths after starting out feeling overwhelmed.'

## nvidia/nemotron-3.5-lightning:free
- server path: endpoint 289 ms, status=ok, shown: 'You completed the breathing exercise.'
- raw (30 s limit): 282 ms, completion_tokens=6, reasoning_tokens=0, passes check=True, reply: 'You completed the exercise.'

## google/gemma-4-26b-a4b-it:free
- server path: endpoint 238 ms, status=error, shown: 'That was seven slow breaths.'
- raw (30 s limit): HTTP 429 after 233 ms: {'message': 'Provider returned error', 'code': 429, 'metadata': {'raw': 'google/gemma-4-26b-a4b-it:free is temporarily rate-limited upstream. Please retry short
```

(The `gemma` raw-call line above is cut at 160 characters by the script; the server-path call for the same model logged `model call failed (mode=live): LLMRequestError` and stored the fallback with status `error`.)

## Conclusion

- With reasoning off, the current model answered in 1.9–2.8 s, with 0 reasoning tokens and 12 output tokens instead of about 90, and passed the output check.
- `nvidia/nemotron-3.5-lightning:free` answered in about 0.3 s, but its replies ("You completed the exercise.") say less than the fixed fallback.
- `google/gemma-4-26b-a4b-it:free` was rate-limited upstream (429). The app fell back as designed.
- **Recommendation:** keep `LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free` with `LLM_REASONING=off` (the default). If latency becomes the priority, `LLM_MODEL=nvidia/nemotron-3.5-lightning:free` is the faster free option, with blander text.
- **Caveat:** these are single calls per model (n = 1–2), so treat them as indicative, not a benchmark. Manual check 2b will add real-browser live runs.
