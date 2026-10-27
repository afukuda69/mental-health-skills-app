"""Compare OpenRouter models for the breathing acknowledgment (diagnostic only).

For each model: one call through the real app endpoint (in-process uvicorn,
LLM_MODE=live, 5 s limit) and one raw call with the app's payload and a 30 s
limit that reports true latency and reasoning-token usage. 2 live calls per
model. Fictional context only. Never prints the key.

    cd backend && .venv/bin/python scripts/compare_models.py MODEL [MODEL ...]
"""

import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

os.environ["LLM_MODE"] = "live"
os.environ.setdefault("SKILLS_DB_PATH", str(Path("/tmp") / f"compare-{uuid.uuid4().hex}.db"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import uvicorn  # noqa: E402

import config  # noqa: E402
import main  # noqa: E402
import model_client  # noqa: E402

PORT = 8012
CTX = {"entry_choice": "overwhelmed", "prior_completed": 0}


def via_server(model: str) -> str:
    os.environ["LLM_MODEL"] = model
    base = f"http://127.0.0.1:{PORT}/api"
    cid = f"compare-{uuid.uuid4().hex[:8]}"
    httpx.post(f"{base}/sessions", json={"client_id": cid, "skill": "breathing", "entry_choice": CTX["entry_choice"]}, timeout=10)
    t0 = time.perf_counter()
    data = httpx.post(f"{base}/sessions/{cid}/acknowledgment", timeout=30).json()
    ms = int((time.perf_counter() - t0) * 1000)
    return f"endpoint {ms} ms, status={data['status']}, shown: {data['text']!r}"


def raw(model: str) -> str:
    payload = model_client.build_payload(model, model_client.build_messages("breathing", CTX))
    headers = {"Authorization": f"Bearer {config.get_llm_api_key()}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    try:
        r = httpx.post(model_client.OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        ms = int((time.perf_counter() - t0) * 1000)
        data = r.json()
        if r.status_code != 200:
            return f"HTTP {r.status_code} after {ms} ms: {str(data.get('error', data))[:160]}"
        usage = data.get("usage") or {}
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        text = " ".join((data["choices"][0]["message"]["content"] or "").split())
        return (f"{ms} ms, completion_tokens={usage.get('completion_tokens')}, reasoning_tokens={reasoning}, "
                f"passes check={model_client.check_output(text)}, reply: {text[:140]!r}")
    except Exception as exc:
        return f"failed after {int((time.perf_counter() - t0) * 1000)} ms: {type(exc).__name__}"


def run(models: list[str]) -> None:
    server = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.1)
    print(f"reasoning: {'on' if config.get_llm_reasoning() else 'off'}  app timeout: {model_client.TIMEOUT_S} s\n")
    for model in models:
        print(f"## {model}")
        print(f"- server path: {via_server(model)}")
        time.sleep(1)
        print(f"- raw (30 s limit): {raw(model)}\n")
        time.sleep(1)
    server.should_exit = True


if __name__ == "__main__":
    run(sys.argv[1:] or [config.get_llm_model()])
