# Final automated checks for manual-checks rows 2b, 4a, 4b, 6, 7, 8

Run on 2026-11-04 on macOS with Playwright driving headless Chromium, on the current look. Fictional data only. Four separate backend and frontend pairs, each with its own scratch SQLite file; `backend/skills.db` was not used. Ports: mock 8093/5293, mock_error 8094/5294, mock_timeout 8095/5295, live 8096/5296. All were checked as free first, and each was confirmed as owned by the process started for this run.

**Live model calls:** 1 (`nvidia/nemotron-3-ultra-550b-a55b:free`, row 2b). The live backend ran with `LLM_MAX_CALLS=3`.

Script: [final/final-run.mjs](final/final-run.mjs). Screenshots: [final/](final/).

| Row | Mode | Console / response | Database | Result |
|---|---|---|---|---|
| 2b | live | `[model] acknowledgment status=ok latency_ms=731`; `measured_ms=75014` | `model` / `ok` / 731 ms; session completed, 7/7 | Closing text: "You completed seven slow breaths. This was your first paced breathing session." |
| 4a | mock_error | `status=error latency_ms=0`; `measured_ms=75001` | `fallback` / `error`; session completed, 7/7 | Closing text: "That was seven slow breaths." Crisis tab visible during the run |
| 4b | mock_timeout | `status=timeout latency_ms=5006`; `measured_ms=75011` | `fallback` / `timeout` / 5006 ms; session completed, 7/7 | Same fallback text. The closing wasn't delayed. Crisis tab visible during the run |
| 6 | mock | Navigated to `about:blank` during cycle 2 | `left`, measured_ms 16450, steps 1 | **Navigation away, not a real tab close.** Headless `page.close()` sends nothing ([browser-run.md](browser-run.md)), so a real tab close couldn't be automated |
| 7 | mock | `"status":"scripted","crisis":true` | user row with empty text and `crisis_flag=1`; scripted row with `crisis_flag=1` | No `model_client` line in the backend log for this mock server |
| 8 | mock | `measured_ms=75018 pauses_ms=0 crisis_ms=10116` | session completed, crisis_ms 10116, measured_ms 75018 | Caption "Cycle 2 of 7" before opening the panel, after 10 s in it, and after closing it |

## Row 7 commands and responses

```text
$ curl -s -X POST localhost:8093/api/sessions -H "Content-Type: application/json" -d {"client_id":"manual-crisis","skill":"reframe"}
{"id":1,"client_id":"manual-crisis","skill":"reframe","entry_choice":null,"started_at":"2026-11-04T17:27:31.232+00:00","

$ curl -s -X POST localhost:8093/api/sessions/manual-crisis/messages -H "Content-Type: application/json" -d {"text":"Fictional test phrase: I want to die"}
{"text":"Crisis support is open. It lists people you can call or text right now.","status":"scripted","latency_ms":null,"crisis":true}
```

## Browser results (raw)

```json
{
  "row4a_mock_error": {
    "console": [
      "[timing] setup_ms=217 (entry and skill pick, reported separately)",
      "[model] acknowledgment status=error latency_ms=0",
      "[timing] exercise measured_ms=75001 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed"
    ],
    "tabs_during": [
      "Crisis"
    ],
    "closing_text": "That was seven slow breaths."
  },
  "row4b_mock_timeout": {
    "console": [
      "[timing] setup_ms=207 (entry and skill pick, reported separately)",
      "[model] acknowledgment status=timeout latency_ms=5006",
      "[timing] exercise measured_ms=75011 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed"
    ],
    "tabs_during": [
      "Crisis"
    ],
    "closing_text": "That was seven slow breaths."
  },
  "row2b_live": {
    "console": [
      "[timing] setup_ms=179 (entry and skill pick, reported separately)",
      "[model] acknowledgment status=ok latency_ms=731",
      "[timing] exercise measured_ms=75014 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed"
    ],
    "tabs_during": [
      "Crisis"
    ],
    "closing_text": "You completed seven slow breaths. This was your first paced breathing session."
  },
  "row8_crisis": {
    "console": [
      "[timing] setup_ms=57 (entry and skill pick, reported separately)",
      "[model] acknowledgment status=mock latency_ms=0",
      "[timing] exercise measured_ms=75018 pauses_ms=0 crisis_ms=10116 planned_ms=75000 end_reason=completed"
    ],
    "caption": {
      "before": "Cycle 2 of 7",
      "after_10s_in_panel": "Cycle 2 of 7",
      "after_close": "Cycle 2 of 7"
    }
  },
  "row6_navigate_away": {
    "console": [
      "[timing] setup_ms=130 (entry and skill pick, reported separately)"
    ]
  }
}
```

## Databases after the run

### mock (rows 6, 7, 8)

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | manual-crisis | reframe |  |  | 0 | 0 |  |  |  |  |  |  |  | 2026-11-04T17:27:31.232+00:00 |  |
| 2 | 8ae877d1-89c7-4297-822b-76eac2343c6e | breathing |  | completed | 1 | 0 | 57 | 75000 | 75018 | 0 | 10116 | 7 | 7 | 2026-11-04T17:27:40.149Z | 2026-11-04T17:29:05.285+00:00 |
| 3 | 07d490eb-d85c-4863-9812-6e71b036f853 | breathing |  | left | 0 | 1 | 130 | 75000 | 16450 | 0 | 0 | 7 | 1 | 2026-11-04T17:27:40.222Z | 2026-11-04T17:27:56.677+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 1 | user |  |  |  | 1 | 2026-11-04T17:27:31.240+00:00 |
| 2 | 1 | scripted | Crisis support is open. It lists people you can call or text right now. | scripted |  | 1 | 2026-11-04T17:27:31.241+00:00 |
| 3 | 2 | model | You took seven slow breaths. | mock | 0 | 0 | 2026-11-04T17:28:55.272+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|

### mock_error (row 4a)

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | c2cbe34a-0465-43ac-9457-dbe6bff6b928 | breathing | tense | completed | 1 | 0 | 217 | 75000 | 75001 | 0 | 0 | 7 | 7 | 2026-11-04T17:27:40.282Z | 2026-11-04T17:28:55.284+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 1 | fallback | That was seven slow breaths. | error | 0 | 0 | 2026-11-04T17:28:45.285+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|

### mock_timeout (row 4b)

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ad22a840-b6a0-4c32-bd05-94b86e3a8d4e | breathing | tense | completed | 1 | 0 | 207 | 75000 | 75011 | 0 | 0 | 7 | 7 | 2026-11-04T17:27:40.271Z | 2026-11-04T17:28:55.284+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 1 | fallback | That was seven slow breaths. | timeout | 5006 | 0 | 2026-11-04T17:28:50.291+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|

### live (row 2b)

## sessions

| id | client_id | skill | entry_choice | end_reason | completed | exited_early | setup_ms | planned_ms | measured_ms | pauses_ms | crisis_ms | steps_planned | steps_completed | started_at | ended_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | e53132c6-80de-44c2-a1d6-d5776234bded | breathing | tense | completed | 1 | 0 | 179 | 75000 | 75014 | 0 | 0 | 7 | 7 | 2026-11-04T17:27:40.252Z | 2026-11-04T17:28:55.271+00:00 |

## messages

| id | session_id | role | text | model_status | latency_ms | crisis_flag | created_at |
|---|---|---|---|---|---|---|---|
| 1 | 1 | model | You completed seven slow breaths. This was your first paced breathing session. | ok | 731 | 0 | 2026-11-04T17:28:46.002+00:00 |

## feedback

| id | session_id | rating |
|---|---|---|
