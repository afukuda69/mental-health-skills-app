# Example: the exact context sent to the chat model

Fictional data only. Generated on 2026-10-29 from a scratch database seeded with `backend/scripts/seed_demo.py` (5 fictional sessions; display name "Alex"; last check-in "Okay"), using the real `model_client.build_chat_messages`.

What is sent:
1. The fixed system prompt.
2. One line per skill from `shared/skills.json`.
3. The profile summary: name, usual skill and its source, last check-in, and per-skill counts.
4. The last 10 messages of **this conversation only**. Here there are 3.

What is **never** sent: other conversations' text, reframe text (it is never stored), acknowledgment or reflection text from exercises, and message text of any kind in the profile summary.

```json
[
  {
    "role": "system",
    "content": "You are the optional chat in a coursework prototype app that guides three short self-guided skills. This is not therapy, diagnosis, or a support service, and nobody monitors it. Users are asked to use fictional scenarios. Answer in plain, calm, non-clinical language, at most 60 words. You may ask one short question. Only describe the three skills as given below. Never invent techniques, add steps, or change their steps or timing. Never diagnose, never mention disorders, therapy, or medication, never praise or cheer, never use exclamation marks, and never claim to remember, watch over, or monitor the user. If one skill fits what the user describes, you may offer it; the user decides. Reply with JSON only: {\"reply\": \"<text>\", \"offer_skill\": \"breathing\" | \"stop\" | \"reframe\" | null}."
  },
  {
    "role": "system",
    "content": "The three skills:\n- breathing: Paced breathing. Breathe in for 4 seconds and out for 6, seven times, following a circle.\n- stop: STOP. Pause, step back, notice, then choose what to do next, one short prompt at a time.\n- reframe: Cognitive reframe. Write down one thought, what supports it, and another way to see it. Typing is optional.\n\nAbout this user, from the local profile (no message text): Name: Alex. Usual skill: Paced breathing [breathing], learned. Last check-in: Okay, just want a minute. Sessions: Paced breathing 2 completed, 1 stopped; STOP 1 completed; Cognitive reframe 1 completed."
  },
  {
    "role": "user",
    "content": "Fictional scenario: I have a class presentation in an hour."
  },
  {
    "role": "assistant",
    "content": "Hi Alex. For a moment like that, your usual skill, Paced breathing, may fit. You can start it below, or choose another."
  },
  {
    "role": "user",
    "content": "Fictional: what does the breathing one involve?"
  }
]
```

Reply in `LLM_MODE=mock` (status `mock`, offer `None`):

> Hi Alex. Your usual skill here is Paced breathing. I can explain it or either of the other two skills. What would you like to look at?
