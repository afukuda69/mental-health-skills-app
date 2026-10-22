# Mental Health Skills Prototype (Assignment 3)

> **Coursework prototype only.** This is a Penn State course project. It is not therapy, not a diagnostic tool, and not a mental health support service. It does not monitor anyone. Do not use it, or recommend it to anyone, as something to rely on in a difficult moment. All testing uses fictional scenarios.
>
> If you are in crisis in the US: call or text **988** (Suicide & Crisis Lifeline), text **HOME to 741741** (Crisis Text Line), or call **911** in an emergency.

## Purpose

A small localhost app that guides one short, structured skill at a time:

- **Paced breathing (4-in / 6-out)**: core skill, built in Part 3.2
- **STOP**: added in Part 3.3
- **One-minute cognitive reframe**: added in Part 3.3

The app controls each skill's steps, timing, exits, saved state, and crisis access. A language model only writes short, neutral acknowledgments. The design is based on the study findings R1–R4 and D1–D6 in Assignment 3 overview (Canvas).

## Planned stack

- Frontend: Vue 3 + Vite
- Backend: FastAPI (Python)
- Storage: SQLite (local file)
- Runs on localhost only. Development on Windows / PowerShell.

## How to run

Coming in Part 3.2.

## Documents

| File | Contents |
|---|---|
| [docs/design.md](docs/design.md) | Main design: flow, screens, timing, model role, crisis access, data, findings mapping |
| [docs/reused.md](docs/reused.md) | What is adapted from the travel app / RAG chatbot |
| [docs/evidence-log.md](docs/evidence-log.md) | Curated evidence log |
| [AGENTS.md](AGENTS.md) | Rules for coding agents |
| [AI-USE.md](AI-USE.md) | AI tool disclosure |
| [report.md](report.md) | Part 3.1 submission |
