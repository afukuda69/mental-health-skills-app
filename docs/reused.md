# Reused from earlier work

Source: the travel application (Assignments 1–2) and the RAG hotel chatbot. Paths refer to that repo.

| From travel app | How it is adapted here |
|---|---|
| FastAPI layout: thin `main.py` routes, logic in `controller.py`, schema and connection in `models.py`, raw `sqlite3` with no ORM | Same split: `main.py` / `sessions.py` / `db.py`. The tables (`sessions`, `messages`, `feedback`) are new; only the layout and raw-`sqlite3` pattern are reused. |
| LLM-call wrapper `chat._call_openrouter` (`httpx`, config from `.env`, typed errors: not configured, rate limited, request error) | Becomes `model_client.py`. The timeout drops from 30 s to **5 s**. On any error the app returns a fixed fallback instead of an error message to the user. An output check is added (length, `?`/`!`, banned words). |
| System prompt plus supplied context (the chatbot was given the saved-hotel schema and rules) | The context is now minimal (skill, entry choice, one count, or the step-3 text). The prompt limits output to a one- or two-sentence acknowledgment. Unlike the chatbot, the model output **never** drives app behavior. |
| Sentinel and guard pattern (`INSUFFICIENT_DATA`, read-only refusal, SQL authorizer): don't trust the model, validate in code | Same principle: the app validates output and falls back. It does not rely on the prompt. |
| Mocked model tests (`@patch("chat._call_openrouter")` in `backend/tests/test_chat_route.py`) | The same approach is used for timeout, error, rejected-output, and success cases. |
| Vue chat component `HotelChat.vue` (fetch to `/api/chat`, loading/error state, quick-question chips) | The chips pattern becomes reframe quick-select chips. The loading/error handling becomes the fallback display. The free-form chat layout is **not** reused (see design.md §j). |
| `theme.css` tokens | Restyled to a muted, low-saturation palette (D6). |
| AGENTS.md / README / report.md / prompts conventions | Same documentation practice. |

**Conversation history: not reused.** I searched the whole travel application (backend, frontend, tests, docs, prompts, handoffs) for history, conversation, chat, message, and session, and listed the tables in `backend/travel.db`. The chatbot does not save or load conversation history:

- `POST /api/chat` (`backend/main.py`) passes a single question to `chat.answer_question`. No earlier turns are sent or stored.
- `frontend/src/components/HotelChat.vue` keeps only the current question and result in component state.
- `travel.db` has no chat or message table (only `bookings`, `demo_hotel_nights`, `hotels`, `saved_hotel_zip_searches`, `saved_hotels`, `trips`, `users`).

So the `messages` table is new work. The RAG chatbot pattern reused is the LLM call plus context wrapper only (`chat._call_openrouter` with the system prompt and supplied context), as listed in the table above.
