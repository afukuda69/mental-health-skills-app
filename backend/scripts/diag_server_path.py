"""Compare the server acknowledgment path with a direct call (diagnostic only).

Starts the real app in-process on port 8011 with LLM_MODE=live, wraps
model_client._call_openrouter to record queue delay and true completion time
(even after the app has given up at 5 s), and alternates with a direct
streamed request using the same URL, headers, and payload, timestamping the
response headers and the first body bytes. Fictional context only. Never
prints the key.

    cd backend && .venv/bin/python scripts/diag_server_path.py 2     # 2 pairs = 4 live calls
"""

import os
import sys
import threading
import time
import uuid
from pathlib import Path

os.environ["LLM_MODE"] = "live"
os.environ.setdefault("SKILLS_DB_PATH", str(Path("/tmp") / f"diag-{uuid.uuid4().hex}.db"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import uvicorn  # noqa: E402

import config  # noqa: E402
import main  # noqa: E402
import model_client  # noqa: E402

PORT = 8011
records = []
_original_call = model_client._call_openrouter
_original_ack = model_client.acknowledge
_submitted = {}


def traced_ack(skill, context):
    _submitted[threading.get_ident()] = time.perf_counter()
    return _original_ack(skill, context)


def traced_call(messages):
    rec = {"thread_start": time.perf_counter(), "submitted": max(_submitted.values()) if _submitted else None}
    records.append(rec)
    try:
        rec["reply"] = _original_call(messages)
        rec["outcome"] = "reply"
    except Exception as exc:
        rec["outcome"] = type(exc).__name__
    rec["end"] = time.perf_counter()
    return rec.get("reply")


model_client.acknowledge = traced_ack
model_client._call_openrouter = traced_call
main.sessions.model_client.acknowledge = traced_ack


def server_call(i: int) -> dict:
    cid = f"diag-server-{i}-{uuid.uuid4().hex[:6]}"
    base = f"http://127.0.0.1:{PORT}/api"
    httpx.post(f"{base}/sessions", json={"client_id": cid, "skill": "breathing", "entry_choice": "tense"}, timeout=10)
    t0 = time.perf_counter()
    data = httpx.post(f"{base}/sessions/{cid}/acknowledgment", timeout=30).json()
    return {"endpoint_ms": int((time.perf_counter() - t0) * 1000), "status": data["status"], "app_latency_ms": data["latency_ms"]}


def direct_streamed_call() -> dict:
    payload = {
        "model": config.get_llm_model(),
        "messages": model_client.build_messages("breathing", {"entry_choice": "tense", "prior_completed": 0}),
        "temperature": 0,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {config.get_llm_api_key()}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    out = {"first_bytes": None}
    with httpx.stream("POST", model_client.OPENROUTER_URL, headers=headers, json=payload, timeout=60) as r:
        out["headers_ms"] = int((time.perf_counter() - t0) * 1000)
        out["http_status"] = r.status_code
        body = b""
        for chunk in r.iter_bytes():
            if out["first_bytes"] is None:
                out["first_byte_ms"] = int((time.perf_counter() - t0) * 1000)
                out["first_bytes"] = chunk[:24]
            body += chunk
    out["total_ms"] = int((time.perf_counter() - t0) * 1000)
    out["leading_whitespace_bytes"] = len(body) - len(body.lstrip())
    try:
        import json

        data = json.loads(body)
        usage = data.get("usage") or {}
        out["reasoning_tokens"] = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        out["completion_tokens"] = usage.get("completion_tokens")
        out["reply"] = " ".join((data["choices"][0]["message"]["content"] or "").split())[:120]
    except Exception as exc:
        out["reply"] = f"(unparsed: {type(exc).__name__})"
    return out


def main_run(pairs: int) -> None:
    server = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.1)
    print(f"model: {config.get_llm_model()}  app timeout: {model_client.TIMEOUT_S} s\n")
    for i in range(pairs):
        s = server_call(i)
        print(f"server #{i + 1}: {s}")
        time.sleep(1)
        d = direct_streamed_call()
        print(f"direct #{i + 1}: {d}")
        time.sleep(1)

    deadline = time.time() + 60  # let abandoned server calls finish so their true latency is known
    while any("end" not in r for r in records) and time.time() < deadline:
        time.sleep(0.5)
    print("\nserver-path model calls (true timing, measured inside the worker thread):")
    for n, r in enumerate(records, 1):
        queue_ms = int((r["thread_start"] - r["submitted"]) * 1000) if r["submitted"] else None
        total = int((r["end"] - r["thread_start"]) * 1000) if "end" in r else "still running after 60 s"
        reply = " ".join((r.get("reply") or "").split())[:100]
        print(f"  #{n}: queue_delay_ms={queue_ms} call_ms={total} outcome={r.get('outcome')} reply={reply!r}")
    server.should_exit = True


if __name__ == "__main__":
    main_run(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
