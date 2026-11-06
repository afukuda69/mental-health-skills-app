# Assignment 3.3 — Integration, Evaluation, and Demonstration: Submission

- **Repository:** `https://github.com/afukuda69/mental-health-skills-app`
- **Commit:** `15d8789111ac422d3d90e03166356d4e464aa833`
- **Demo recording:** https://drive.google.com/file/d/1XvEnZMhjCs-gEkbN3QMfMkP5o-wpRKON/view?usp=drive_link
- **Process screencast:** Not recorded. The failure, evidence, and decision are documented in writing instead: see [docs/evidence/3.2/server-path-diagnosis.md](docs/evidence/3.2/server-path-diagnosis.md) and the OpenRouter timeout entry in [docs/evidence-log.md](docs/evidence-log.md).

The app is called **Tidebreak**. This submission is late.

## Documents and evidence

- [README.md](README.md): setup from a clean checkout (bash, plus PowerShell), settings, what is saved, tests
- [docs/design.md](docs/design.md): the design, every change since 3.1 with the finding behind it (§l), and closed questions (§k)
- [docs/evaluation.md](docs/evaluation.md): 28 scenarios, 3 behavior checks, live checks, a surprising finding, and an untested limitation
- [docs/evidence-log.md](docs/evidence-log.md): prompts, changes, observations, and decisions, including failures
- [docs/reused.md](docs/reused.md): what was adapted from the travel app and the RAG chatbot
- [AI-USE.md](AI-USE.md): AI tools and models
- Evidence in [docs/evidence/3.3/](docs/evidence/3.3/):
  - [evaluation-run.md](docs/evidence/3.3/evaluation-run.md): checks, console lines, and requests for each scenario
  - [live-chat-eval.md](docs/evidence/3.3/live-chat-eval.md): live model replies, raw and shown
  - [a11y.md](docs/evidence/3.3/a11y.md) and [screens/](docs/evidence/3.3/screens/): accessibility scan, and every screen at 375 and 1280 px
  - [clean-checkout.md](docs/evidence/3.3/clean-checkout.md): following the README from a fresh clone
  - [chat-context-example.md](docs/evidence/3.3/chat-context-example.md): the exact context sent to the model
  - [pytest-output.txt](docs/evidence/3.3/pytest-output.txt), [vitest-output.txt](docs/evidence/3.3/vitest-output.txt), [build-output.txt](docs/evidence/3.3/build-output.txt)
  - [screencast-plan.md](docs/evidence/3.3/screencast-plan.md): the demo script, and the plan for the process screencast, which was not recorded
- Failure documented in place of the process screencast: [server-path-diagnosis.md](docs/evidence/3.2/server-path-diagnosis.md)

## What is complete

- **Three skills:** paced breathing, STOP, and the cognitive reframe, one step per screen, each planned at 90 s or less.
- **Personalization with control:** the usual skill is learned from history with no setup. An optional check-in changes what is suggested, and the user can change it. Profile shows each item's source, with a way to change it and Reset to learned.
- **Model use, limited:** a closing acknowledgment, the reframe reflection, and an optional chat that can offer a skill. Output is checked in code, with a 5 s wall-clock deadline and fixed fallbacks. The model never writes or changes steps, and never starts a skill.
- **Safety:** a static Crisis tab on every screen, independent of the backend, the model, and any detection. A supplementary phrase check runs before the model. Stop is one tap with no dialog.
- **Persistence:** sessions, conversations, feedback, and a local profile in SQLite, with History and Delete all. Typed reframe and STOP text is never stored.
- **Revisited from 3.1:** 28 logged changes in [design.md §l](docs/design.md). The main ones: the check-in now shapes suggestions; a Profile exists, against my earlier "no settings"; reframe text is no longer stored; and an optional chat was added without becoming chat-first.

## What the evidence shows

- **Evaluation, mocked:** 28 of 28 scenarios passed in a real browser, covering ordinary use, interruptions, and failures.
- **Behavior checks:** all 3 held. Crisis opened 24 times across 12 scenarios, with no network request, including 12 times after a failed request or with the backend down. No typed text was stored or sent, apart from the permitted step-3 answer. The longest exercise was 75.0 s, with pauses and crisis time excluded. Deliberately breaking the app made these checks fail, so they can detect a problem.
- **Timing at a reading pace:** STOP took 52.1 s (60 s planned) and the reframe 54.2 s (70 s planned), with a simulated reader.
- **Automated tests:** 104 backend and 38 frontend, all mocked. The build passes.
- **Accessibility:** axe scanned 27 screen states at 3 widths: 0 violations and no horizontal overflow. A planted problem was flagged.
- **Clean checkout:** the README worked from a fresh clone on macOS. The run found one bug, now fixed.
- **Live model, 8 calls, separate from the above:** all finished within 5 s. **Surprising finding:** replies did not use the name or say "your usual", although the mock does. So the mocked chat scenario shows that context is delivered, not that the model personalizes. A good refusal was blocked for containing "diagnose", and the fallback replaced it. An indirect fictional statement got a gentle reply with no crisis pointer, which is why the Crisis tab, not detection, is the safety route.

These checks establish software behavior with fictional scenarios. They say nothing about clinical effectiveness or how the app feels to use.

## Unresolved

- **The process screencast is missing.** It was not recorded. The failure, evidence, and decision are documented in writing instead, as linked at the top of this report.
- **No peer or user testing.** The check-in wording, the cycle counter, and the value of the acknowledgment are design decisions that no person has tried.
- **Real tab close** is untested. Leaving is verified by navigating away and hiding the page, but headless browsers send nothing on close.
- **Not tested:** a real screen reader, browsers other than Chromium, and Windows. The PowerShell commands in the README have not been run.
- **Chat tailoring is weak with the live model,** and only 8 live calls were made in this evaluation. The free model has been much slower at other times.
- **The phrase list** misses indirect wording and other languages, and gives false positives on idioms.
- **Crisis resources** are US-only.
