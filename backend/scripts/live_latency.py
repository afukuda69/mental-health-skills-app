"""Measure live model latency for the breathing acknowledgment.

Makes N live calls (default 12, max 20) through model_client._call_openrouter
with a 30 s limit, so slow replies are measured rather than cut off, then
reports what the app's real 5 s rule would have shown. Uses fictional
contexts only. Never prints the API key.

    cd backend && .venv/bin/python scripts/live_latency.py 12
"""

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import model_client  # noqa: E402

CONTEXTS = [
    {"entry_choice": "tense", "prior_completed": 0},
    {"entry_choice": "overwhelmed", "prior_completed": 1},
    {"entry_choice": "okay", "prior_completed": 3},
    {"entry_choice": None, "prior_completed": 0},
]


def main(n: int) -> None:
    n = max(1, min(n, 20))
    model_client.TIMEOUT_S = 30.0
    print(f"model: {config.get_llm_model()}")
    print(f"calls: {n} (raw provider latency, 30 s limit; app limit is 5 s)\n")
    print("| # | entry | latency_ms | passes check | app would show | reply |")
    print("|---|---|---|---|---|---|")
    latencies, shown_model = [], 0
    for i in range(n):
        ctx = CONTEXTS[i % len(CONTEXTS)]
        started = time.perf_counter()
        try:
            reply = model_client._call_openrouter(model_client.build_messages("breathing", ctx)) or ""
            error = None
        except Exception as exc:
            reply, error = "", type(exc).__name__
        ms = int((time.perf_counter() - started) * 1000)
        latencies.append(ms)
        ok = model_client.check_output(reply.strip())
        if error:
            outcome = f"fallback ({error})"
        elif ms > 5000:
            outcome = "fallback (timeout)"
        elif not ok:
            outcome = "fallback (rejected)"
        else:
            outcome = "model text"
            shown_model += 1
        clean = " ".join(reply.split()).replace("|", "/")[:160] or "(empty)"
        print(f"| {i + 1} | {ctx['entry_choice']} | {ms} | {ok} | {outcome} | {clean} |")
        time.sleep(1.0)

    s = sorted(latencies)
    print(f"\nlatency ms: min {s[0]}, median {int(statistics.median(s))}, max {s[-1]}")
    print(f"under 5000 ms: {sum(1 for x in s if x <= 5000)}/{n}")
    print(f"model text shown under the app's rules: {shown_model}/{n}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
