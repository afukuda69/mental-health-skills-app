# Assignment 3.1 — Research and Design: Submission

- **Repository:** `https://github.com/afukuda69/mental-health-skills-app`
- **Commit:** `7e5b7cd638587420fbd9408db7edd8a75b98d18b`

> Coursework prototype. It is not therapy or diagnosis, and not for use in a real crisis.

## Documents

- [README.md](README.md): purpose, disclaimer, stack
- [docs/design.md](docs/design.md): flow diagram, screens, timing, model role, crisis access, data model, personalization, findings mapping, alternatives, open questions
- [docs/reused.md](docs/reused.md): what is adapted from the travel app / RAG chatbot
- [AGENTS.md](AGENTS.md): rules and constraints for coding agents
- [docs/evidence-log.md](docs/evidence-log.md): evidence log
- [AI-USE.md](AI-USE.md): AI tool disclosure

## What is complete

- Design for three skills: paced breathing (core, Part 3.2), STOP, and the one-minute reframe (Part 3.3). Each has exact step wording and runs one step per screen.
- A Mermaid user flow, including the Stop exercise and Crisis support paths, and the model-failure fallback.
- A timing budget per skill (breathing ~75 s, STOP ~60 s, reframe ~70–85 s) with stated assumptions.
- A limited model role with enforced output checks, a 5 s timeout, and fixed fallback text.
- A static crisis route that does not depend on the backend or the model. The keyword check is documented as a supplement, with its limits.
- A SQLite data model, and a statement of what is shown, stored, and not stored.
- History-derived personalization ("Use my usual"), with the trade-offs stated.
- A mapping table that covers R1–R4 and D1–D6, plus rejected alternatives.

## What the evidence shows

This milestone is design only. No working app is expected or claimed. The evidence consists of the design documents and the evidence-log entries. The log includes one revised decision: the exit button was renamed to "Stop exercise". The timing figures are planned estimates, not measurements.

## Unresolved

1. Should history show the user's own typed reframe text? (Default: no. Shown only on a deliberate tap? Never?)
2. Should the entry choice influence which skill is labelled as suggested, or should only history do that?
3. Entry option wording: are "Tense or wound up / Overwhelmed / Okay, just want a minute" neutral enough (D6)?
4. Does the "3 of 7" breathing counter help people know when it ends, or add demand (D3, D6)?
5. Does the model's breathing acknowledgment add anything over the fixed fallback? To be evaluated in 3.2 with mocked and live calls.
6. Should the user be able to clear history? This is a control, not configuration, but it adds a screen.
7. Should crisis-panel opens be counted (with no content) to support the evaluation, or left unrecorded as now?
8. Is 5 s the right model timeout for the chosen provider? To be measured in 3.2.
9. Crisis resources are US-only. Is that acceptable for a localhost coursework prototype? Note it in the README.
10. After Stop exercise, should the user go to Done (current) or straight back to entry?
