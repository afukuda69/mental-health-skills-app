# AI use disclosure

| Tool | Model / identifier | Where used | Role |
|---|---|---|---|
| Claude Code (VS Code extension) | Claude Opus 5.5 (`claude-opus-5-5`) | Part 3.1 | Drafted the design documentation (README, AGENTS.md, docs/design.md, docs/reused.md, docs/evidence-log.md, report.md) from my stated design decisions and the assignment text. Flagged conflicts with the assignment. I chose all design decisions. |
| Claude Code 2.1.201 (VS Code extension) | Claude Opus 5.5 (`claude-opus-5-5`) | Part 3.2 | Wrote the backend, frontend, and tests from docs/design.md and my 3.2 brief. Ran the tests, endpoint checks, live latency runs, and a headless browser run (Playwright, not part of the app), and drafted the 3.2 docs and report. I answered the planning questions (crisis check scope, live key, crisis data, git) and reviewed the output. |
| App runtime model, via OpenRouter | `nvidia/nemotron-3-ultra-550b-a55b:free` | Part 3.2+ | Writes the short breathing acknowledgment only (see docs/design.md §e). Output is checked in code and replaced with fixed text on any failure. Tests use mocks. |

I reviewed all generated text. The evidence log records selected prompts and decisions: [docs/evidence-log.md](docs/evidence-log.md).
