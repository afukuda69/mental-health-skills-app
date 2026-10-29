"""Live check of the chat model's JSON replies (diagnostic only, counts toward the live-call cap).

Calls model_client.chat_reply with the real context builder for N fictional
messages (default 4, max 10). Prints status, latency, offer_skill, and the reply
or the fallback. Never prints the key.

    cd backend && .venv/bin/python scripts/live_chat_check.py 4
"""

import os
import sys
from pathlib import Path

os.environ["LLM_MODE"] = "live"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chat  # noqa: E402
import config  # noqa: E402
import model_client  # noqa: E402

PROMPTS = [
    "Fictional scenario: a student is nervous before a class presentation. What could help?",
    "Explain the breathing rhythm in this app.",
    "What is the STOP skill for?",
    "Fictional: a student keeps thinking they failed an exam before getting results.",
    "Can you tell me if I have anxiety?",
]


def main(n: int) -> None:
    n = max(1, min(n, 10))
    print(f"model: {config.get_llm_model()}  reasoning: {'on' if config.get_llm_reasoning() else 'off'}\n")
    print("| # | prompt | status | latency_ms | offer_skill | shown text |")
    print("|---|---|---|---|---|---|")
    skills = chat.load_skills()
    for i in range(n):
        prompt = PROMPTS[i % len(PROMPTS)]
        msgs = model_client.build_chat_messages(skills, "breathing x2 completed", [{"role": "user", "text": prompt}])
        r = model_client.chat_reply(msgs)
        print(f"| {i + 1} | {prompt} | {r.status} | {r.latency_ms} | {r.offer_skill} | {r.reply} |")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
