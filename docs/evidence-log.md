# Evidence log

Curated and redacted. No credentials, personal information, or research-participant information.

| Date | Prompt / Action | Change | Observation | Decision |
|---|---|---|---|---|
| 2026-10-22 | Asked Claude Code to draft the Part 3.1 docs from my stated design decisions and the assignment text | Created README.md, AGENTS.md, docs/design.md, docs/reused.md, docs/evidence-log.md, AI-USE.md, report.md | Claude flagged a conflict: Part 3.2 requires demonstrating the model's contribution, but breathing (the 3.2 core skill) had no model role. It also found no chat-history table in the travel app's `models.py`. | Added a model closing acknowledgment to breathing, with a fixed fallback. Marked the history-persistence reuse claim "to verify". Resolved in the chat-history search row below. |
| 2026-10-22 | **Revised approach:** exit button labelled "Stop" | Renamed it "Stop exercise" in all docs | "Stop" clashed with step 1 of the STOP skill ("Stop."). On STOP screens, the exit control and the skill instruction would read the same. | Use "Stop exercise". Re-check in 3.2 with the running UI. |
| 2026-10-22 | Asked Claude Code to search the whole travel application for where chatbot conversation history is saved or loaded (terms: history, conversation, chat, message, session) | Updated docs/reused.md: replaced the "to verify" note with the search result | Searched backend, frontend, tests, docs, prompts, and handoffs, and listed the `travel.db` tables. Nothing found: `/api/chat` handles one question per request, `HotelChat.vue` keeps only the current question and result, and `travel.db` has no chat or message table. | The `messages` table counts as new work. The only RAG chatbot pattern reused is the LLM call + context wrapper. |
| | *(failed or revised approach: to fill in during 3.2/3.3)* | | | |
| | | | | |
