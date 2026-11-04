# Evaluation run (mocked model)

Generated from [evaluation-results.json](evaluation-results.json), written by [e2e/evaluate.mjs](../../../e2e/evaluate.mjs). Run on 2026-11-04 on macOS in headless Chromium: 28 of 28 scenarios passed in 139 s. Each scenario had its own temp database and OS-assigned ports. No live model calls.

## S01

**Paced breathing, full run** (Ordinary use; mock): PASS

- Does: Picks Paced breathing in Activities and follows it to the end, then rates it Helped.
- Expected: Seven cycles, closing text, check-in, Done. Saved as completed, 7/7, about 75 s.
- Observed: Completed 7/7 in 75.0 s. Closing: "You took seven slow breaths.". Rated Helped.

Checks:

- ok: Crisis visible: breathing intro
- ok: Crisis content shown: breathing intro
- ok: Crisis opened with no request: breathing intro
- ok: Crisis visible: breathing closing
- ok: Crisis content shown: breathing closing
- ok: Crisis opened with no request: breathing closing
- ok: Crisis visible: check-in
- ok: Crisis content shown: check-in
- ok: Crisis opened with no request: check-in
- ok: Crisis visible: done
- ok: Crisis content shown: done
- ok: Crisis opened with no request: done
- ok: completed 7/7

Crisis opened from: breathing intro, breathing closing, check-in, done

Console:

```text
[timing] setup_ms=50 (entry and skill pick, reported separately)
[model] acknowledgment status=mock latency_ms=0
[timing] exercise measured_ms=75011 pauses_ms=0 crisis_ms=33 planned_ms=75000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/acknowledgment
POST /api/sessions/<id>/end
POST /api/sessions/<id>/feedback
```

## S02

**STOP at a reading pace** (Ordinary use; mock): PASS

- Does: Reads each of the four STOP screens for about 13 s, then taps Next.
- Expected: Four steps in order, then check-in. Completed 4/4, under the 60 s plan.
- Observed: Steps: Stop. / Take a step back. / Observe. / Proceed mindfully.. Completed 4/4 in 52.1 s of 60.0 s planned.

Checks:

- ok: steps in design order
- ok: completed 4/4

Console:

```text
[timing] setup_ms=41 (entry and skill pick, reported separately)
[timing] exercise measured_ms=52127 pauses_ms=0 crisis_ms=0 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S03

**Reframe at a reading pace, with typing** (Ordinary use; mock): PASS

- Does: Types a fictional thought, picks a chip, types another view, about 14 s per step, reads the reflection for 12 s.
- Expected: Reflection appears. Only the step-3 answer is sent; nothing typed is stored.
- Observed: Completed 4/4 in 54.2 s of 70.0 s planned. Reflection: "Another way to see it: it may not be as certain as it feels.". Step-3 text sent once, to /reflection. Step-1 text never left the browser.

Checks:

- ok: Crisis visible: reframe step
- ok: Crisis content shown: reframe step
- ok: Crisis opened with no request: reframe step
- ok: step-3 answer sent once, to /reflection only
- ok: step-1 text never sent
- ok: completed
- ok: "FICT-R1" stored nowhere
- ok: "FICT-R1" sent nowhere
- ok: "FICT-R3" stored nowhere
- ok: nothing in browser storage

Crisis opened from: reframe step

Console:

```text
[timing] setup_ms=66 (entry and skill pick, reported separately)
[timing] exercise measured_ms=54217 pauses_ms=0 crisis_ms=32 planned_ms=70000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/reflection
POST /api/sessions/<id>/end
```

## S04

**STOP at its planned budget** (Intended pace; mock): PASS

- Does: Takes the full 15 s on each STOP screen.
- Expected: About 60 s, within 90 s.
- Observed: Completed in 60.1 s of 60.0 s planned.

Checks:

- ok: completed 4/4
- ok: within 90 s

Console:

```text
[timing] setup_ms=48 (entry and skill pick, reported separately)
[timing] exercise measured_ms=60066 pauses_ms=0 crisis_ms=0 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S05

**Reframe at its planned budget, slowest model** (Intended pace; mock_timeout): PASS

- Does: Takes the full 20 s on each input step with the model timing out, then reads for 5 s.
- Expected: The worst planned case: about 70 s plus model wait, within 90 s, with fallback text.
- Observed: Completed in 70.5 s of 70.0 s planned, with "You've noted another way to look at it."

Checks:

- ok: fallback reflection
- ok: completed within 90 s

Console:

```text
[timing] setup_ms=38 (entry and skill pick, reported separately)
[timing] exercise measured_ms=70526 pauses_ms=0 crisis_ms=0 planned_ms=70000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/reflection
POST /api/sessions/<id>/end
```

## S06

**Tense suggests breathing** (Check-in; mock): PASS

- Does: Taps "Tense or wound up" on Home.
- Expected: A breathing suggestion with the reason and a Change link. Nothing starts.
- Observed: Breathing suggested with the reason and Change. No session started. Activities still lists every skill.

Checks:

- ok: suggestion with reason
- ok: no session started by itself
- ok: Crisis visible: home with suggestion
- ok: Crisis content shown: home with suggestion
- ok: Crisis opened with no request: home with suggestion
- ok: all skills still listed

Crisis opened from: home with suggestion

API requests:

```text
GET /api/profile
POST /api/profile
GET /api/profile
```

## S07

**Overwhelmed contracts Home** (Check-in; mock): PASS

- Does: Taps "Overwhelmed", then "Show everything".
- Expected: One big breathing button, Crisis, Show everything; tabs reduced to Crisis. Show everything restores the rest.
- Observed: Tabs during: [Crisis]. After Show everything: [Home,Activities,Chat,Profile,Crisis].

Checks:

- ok: only Crisis in the bar
- ok: one big button
- ok: other content hidden
- ok: Crisis visible: contracted home
- ok: Crisis content shown: contracted home
- ok: Crisis opened with no request: contracted home
- ok: full tabs back

Crisis opened from: contracted home

API requests:

```text
GET /api/profile
POST /api/profile
```

## S08

**Overriding a suggestion** (Check-in; mock): PASS

- Does: Taps Tense, Change, Okay, Change, Skip.
- Expected: Each choice can be undone. Okay shows the usual skill. Skip suggests nothing.
- Observed: Tense, Okay and Skip each applied and could be changed. Okay showed the usual skill. Skip showed no suggestion.

Checks:

- ok: Okay shows the usual skill
- ok: Skip suggests nothing
- ok: last check-in saved

API requests:

```text
GET /api/profile
POST /api/profile
POST /api/profile
POST /api/profile
```

## S09

**Choosing a usual skill, then resetting** (Profile; mock): PASS

- Does: Sets Usual skill to STOP in Profile, checks Home and Activities, then taps Reset to learned.
- Expected: STOP shows as chosen and is used in Home and Activities. Reset returns to the learned skill.
- Observed: Chosen STOP showed in Profile, Home and Activities. Reset returned to Paced breathing, learned.

Checks:

- ok: Crisis visible: profile
- ok: Crisis content shown: profile
- ok: Crisis opened with no request: profile
- ok: Crisis visible: activities
- ok: Crisis content shown: activities
- ok: Crisis opened with no request: activities
- ok: shown as chosen
- ok: Home uses it
- ok: Activities tag follows it
- ok: reset returns to learned

Crisis opened from: profile, activities

API requests:

```text
GET /api/profile
GET /api/profile
GET /api/history
POST /api/profile
GET /api/history
GET /api/profile
POST /api/profile
GET /api/profile
GET /api/profile
GET /api/history
POST /api/profile/reset
GET /api/history
```

## S10

**Usual skill updates from use** (Profile; mock): PASS

- Does: Finishes STOP and rates it Helped, then opens Profile.
- Expected: Counts rise and the learned usual skill becomes STOP.
- Observed: Usual went from Paced breathing to STOP (learned). Counts: Paced breathing: 2 completed, 1 stopped, 0 left; STOP: 2 completed, 0 stopped, 0 left; Cognitive reframe: 1 completed, 0 stopped, 0 left.

Checks:

- ok: usual moved to STOP, learned
- ok: count rose

Console:

```text
[timing] setup_ms=33 (entry and skill pick, reported separately)
[timing] exercise measured_ms=8882 pauses_ms=0 crisis_ms=0 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
GET /api/history
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
POST /api/sessions/<id>/feedback
GET /api/profile
GET /api/profile
GET /api/history
```

## S11

**Reply uses the profile** (Chat; mock): PASS

- Does: Asks for help before a fictional presentation.
- Expected: Reply uses the name and usual skill and offers it. The user taps to start.
- Observed: "Hi Alex. For a moment like that, your usual skill, Paced breathing, may fit. You can start it below, or choose another." with a Start button. No session started.

Checks:

- ok: Crisis visible: chat
- ok: Crisis content shown: chat
- ok: Crisis opened with no request: chat
- ok: tailored
- ok: offer button
- ok: nothing started by itself

Crisis opened from: chat

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
```

## S12

**A request for a diagnosis** (Chat; mock): PASS

- Does: Asks "Can you tell me if I have anxiety?"
- Expected: The limit reply and links to the three skills. No diagnosis.
- Observed: "I can't give a useful reply to that here. This is a coursework prototype and can't assess anything. You can try one of the skills below." with three skill links.

Checks:

- ok: three skill links
- ok: limits bar visible

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
```

## S13

**In the chat** (Crisis phrase; mock): PASS

- Does: Types the fictional phrase "I want to die".
- Expected: Panel opens, scripted reply, no model call, typed text not stored, flag stored.
- Observed: Panel opened. Rows: user (no text, flag 1), scripted (flag 1). No model row.

Checks:

- ok: user row with no text, flag set
- ok: scripted reply, no model status
- ok: "I want to die" stored nowhere
- ok: nothing in browser storage

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
```

## S14

**In the reframe** (Crisis phrase; mock): PASS

- Does: Types the phrase in a reframe step, closes the panel, carries on.
- Expected: Panel opens and pauses. Text stays on screen. It is never sent or stored.
- Observed: Panel opened both times, text kept, crisis_ms 3053. No reflection request; fallback text shown.

Checks:

- ok: text kept after the panel
- ok: crisis time recorded
- ok: no reflection request
- ok: fallback reflection
- ok: "I want to die" stored nowhere
- ok: "I want to die" sent nowhere
- ok: nothing in browser storage

Console:

```text
[timing] setup_ms=42 (entry and skill pick, reported separately)
[timing] exercise measured_ms=9438 pauses_ms=0 crisis_ms=3053 planned_ms=70000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S15

**In the STOP note** (Crisis phrase; mock): PASS

- Does: Opens the optional note on Observe and types the phrase.
- Expected: Panel opens and pauses. The note is never sent or stored.
- Observed: Panel opened, crisis_ms 3027, session completed. Phrase in no request and no table.

Checks:

- ok: crisis time recorded, finished
- ok: "I want to die" stored nowhere
- ok: "I want to die" sent nowhere
- ok: nothing in browser storage

Console:

```text
[timing] setup_ms=131 (entry and skill pick, reported separately)
[timing] exercise measured_ms=9459 pauses_ms=0 crisis_ms=3027 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S16

**Stop mid-exercise** (Interruption; mock): PASS

- Does: Taps Stop exercise during cycle 2.
- Expected: No dialog, no check-in, "Stopped. That's fine." Saved as stopped.
- Observed: Stopped at 15.5 s, 1/7 cycles. No dialog, no check-in.

Checks:

- ok: Crisis visible: breathing running
- ok: Crisis content shown: breathing running
- ok: Crisis opened with no request: breathing running
- ok: Crisis visible: stopped
- ok: Crisis content shown: stopped
- ok: Crisis opened with no request: stopped
- ok: saved as stopped
- ok: no dialog
- ok: no check-in saved

Crisis opened from: breathing running, stopped

Console:

```text
[timing] setup_ms=43 (entry and skill pick, reported separately)
[timing] exercise measured_ms=15455 pauses_ms=0 crisis_ms=33 planned_ms=75000 end_reason=stopped
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
GET /api/profile
```

## S17

**Crisis panel mid-exercise** (Interruption; mock): PASS

- Does: Opens Crisis for 10 s during breathing, then goes back.
- Expected: The cycle holds. Crisis time is stored apart and excluded from measured time.
- Observed: "Cycle 2 of 7" held for the panel. crisis_ms 10048, measured 75.0 s.

Checks:

- ok: cycle held
- ok: crisis time about 10 s

Console:

```text
[timing] setup_ms=36 (entry and skill pick, reported separately)
[model] acknowledgment status=mock latency_ms=0
[timing] exercise measured_ms=75010 pauses_ms=0 crisis_ms=10048 planned_ms=75000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/acknowledgment
POST /api/sessions/<id>/end
```

## S18

**Pause mid-exercise** (Interruption; mock): PASS

- Does: Pauses STOP for 4 s on step 2, then resumes.
- Expected: Pause time is stored apart and excluded.
- Observed: pauses_ms 4015, measured 12.1 s.

Checks:

- ok: pause about 4 s
- ok: pause not in measured time

Console:

```text
[timing] setup_ms=44 (entry and skill pick, reported separately)
[timing] exercise measured_ms=12138 pauses_ms=4015 crisis_ms=0 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S19

**Leaving the page** (Interruption; mock): PASS

- Does: Navigates away during cycle 2.
- Expected: Saved as left, with the active time.
- Observed: Saved as left at 15.4 s.

Checks:

- ok: saved as left

Console:

```text
[timing] setup_ms=42 (entry and skill pick, reported separately)
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
POST /api/sessions/<id>/end
```

## S20

**Hiding the tab and coming back** (Interruption; mock): PASS

- Does: Hides the page during STOP, comes back, resumes, finishes.
- Expected: Saved as left while hidden, paused on return, then completed.
- Observed: While hidden: left. On return: paused. End: completed, pauses_ms 1557.

Checks:

- ok: left, paused, then completed
- ok: hidden time excluded

Console:

```text
[timing] setup_ms=42 (entry and skill pick, reported separately)
[timing] exercise measured_ms=9481 pauses_ms=1557 crisis_ms=0 planned_ms=60000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
POST /api/sessions/<id>/end
```

## S21

**Leaving with typed text on screen** (Interruption; mock): PASS

- Does: Types in the reframe and in the STOP note, then leaves.
- Expected: The session ends as left. The text is sent nowhere and stored nowhere.
- Observed: Saved as left. No request and no table contained the text.

Checks:

- ok: saved as left
- ok: "FICT-LEAVE" stored nowhere
- ok: "FICT-LEAVE" sent nowhere
- ok: nothing in browser storage

Console:

```text
[timing] setup_ms=43 (entry and skill pick, reported separately)
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
POST /api/sessions/<id>/end
```

## S22

**Model error** (Failure; mock_error): PASS

- Does: Uses chat and breathing while the model errors.
- Expected: Fixed fallback in both. Crisis and the exercise keep working.
- Observed: Chat: fixed fallback with skill links. Breathing: "That was seven slow breaths.", 75.0 s. Rows: fallback/error, fallback/error.

Checks:

- ok: Crisis visible: chat after mock_error
- ok: Crisis content shown: chat after mock_error
- ok: Crisis opened with no request: chat after mock_error
- ok: skill links shown
- ok: Crisis visible: breathing closing after mock_error
- ok: Crisis content shown: breathing closing after mock_error
- ok: Crisis opened with no request: breathing closing after mock_error
- ok: status logged
- ok: two fallback rows
- ok: breathing fallback
- ok: chat fallback

Crisis opened from: chat after mock_error, breathing closing after mock_error

Console:

```text
[timing] setup_ms=32 (entry and skill pick, reported separately)
[model] acknowledgment status=error latency_ms=0
[timing] exercise measured_ms=75012 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/acknowledgment
POST /api/sessions/<id>/end
```

## S23

**Model timeout** (Failure; mock_timeout): PASS

- Does: Uses chat and breathing while the model takes too long.
- Expected: Fallback after 5 s in chat. Breathing is not delayed.
- Observed: Chat: fixed fallback with skill links. Breathing: "That was seven slow breaths.", 75.0 s. Rows: fallback/timeout, fallback/timeout.

Checks:

- ok: Crisis visible: chat after mock_timeout
- ok: Crisis content shown: chat after mock_timeout
- ok: Crisis opened with no request: chat after mock_timeout
- ok: skill links shown
- ok: Crisis visible: breathing closing after mock_timeout
- ok: Crisis content shown: breathing closing after mock_timeout
- ok: Crisis opened with no request: breathing closing after mock_timeout
- ok: status logged
- ok: two fallback rows
- ok: breathing fallback
- ok: chat fallback

Crisis opened from: chat after mock_timeout, breathing closing after mock_timeout

Console:

```text
[timing] setup_ms=34 (entry and skill pick, reported separately)
[model] acknowledgment status=timeout latency_ms=5005
[timing] exercise measured_ms=75012 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/acknowledgment
POST /api/sessions/<id>/end
```

## S24

**Malformed model output** (Failure; mock_malformed): PASS

- Does: Uses chat and breathing while the model returns unusable text.
- Expected: Output rejected, fixed fallback in both.
- Observed: Chat: fixed fallback with skill links. Breathing: "That was seven slow breaths.", 75.0 s. Rows: fallback/fallback, fallback/fallback.

Checks:

- ok: Crisis visible: chat after mock_malformed
- ok: Crisis content shown: chat after mock_malformed
- ok: Crisis opened with no request: chat after mock_malformed
- ok: skill links shown
- ok: Crisis visible: breathing closing after mock_malformed
- ok: Crisis content shown: breathing closing after mock_malformed
- ok: Crisis opened with no request: breathing closing after mock_malformed
- ok: status logged
- ok: two fallback rows
- ok: breathing fallback
- ok: chat fallback

Crisis opened from: chat after mock_malformed, breathing closing after mock_malformed

Console:

```text
[timing] setup_ms=34 (entry and skill pick, reported separately)
[model] acknowledgment status=fallback latency_ms=0
[timing] exercise measured_ms=75011 pauses_ms=0 crisis_ms=0 planned_ms=75000 end_reason=completed
```

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/acknowledgment
POST /api/sessions/<id>/end
```

## S25

**Backend down from the start** (Failure; no backend): PASS

- Does: Opens the app with no backend, uses Crisis, Chat, Profile, and a full reframe.
- Expected: Crisis works. Neutral notices. Skills run; the reframe shows its fallback.
- Observed: Crisis opened on 4 screens. Chat and Profile showed neutral notices. Reframe finished with "You've noted another way to look at it."

Checks:

- ok: Crisis visible: home, backend down
- ok: Crisis content shown: home, backend down
- ok: Crisis opened with no request: home, backend down
- ok: Crisis visible: chat, backend down
- ok: Crisis content shown: chat, backend down
- ok: Crisis opened with no request: chat, backend down
- ok: Crisis visible: profile, backend down
- ok: Crisis content shown: profile, backend down
- ok: Crisis opened with no request: profile, backend down
- ok: Crisis visible: reframe, backend down
- ok: Crisis content shown: reframe, backend down
- ok: Crisis opened with no request: reframe, backend down
- ok: fallback reflection
- ok: "FICT-DOWN" stored nowhere
- ok: "FICT-DOWN" sent nowhere
- ok: nothing in browser storage

Crisis opened from: home, backend down, chat, backend down, profile, backend down, reframe, backend down

Console:

```text
[timing] setup_ms=31 (entry and skill pick, reported separately)
[session] write failed: /sessions -> HTTP 500
[timing] exercise measured_ms=9335 pauses_ms=0 crisis_ms=33 planned_ms=70000 end_reason=completed
[session] write failed: /sessions/00387ca9-6b3f-4976-99da-e68d00f70c2f/end -> HTTP 500
```

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/profile
GET /api/history
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/reflection
POST /api/sessions/<id>/end
```

## S26

**Backend stops mid-exercise** (Failure; mock): PASS

- Does: The backend stops during step 2 of STOP.
- Expected: The exercise finishes. Crisis works. The session has no end record.
- Observed: Finished and reached Done. Crisis opened twice. The row has no end reason, so History shows "Not finished".

Checks:

- ok: Crisis visible: STOP after backend stopped
- ok: Crisis content shown: STOP after backend stopped
- ok: Crisis opened with no request: STOP after backend stopped
- ok: Crisis visible: done after backend stopped
- ok: Crisis content shown: done after backend stopped
- ok: Crisis opened with no request: done after backend stopped
- ok: no end record, as expected

Crisis opened from: STOP after backend stopped, done after backend stopped

Console:

```text
[timing] setup_ms=38 (entry and skill pick, reported separately)
[timing] exercise measured_ms=9481 pauses_ms=0 crisis_ms=33 planned_ms=60000 end_reason=completed
[session] write failed: /sessions/9f3da6d3-ed07-4e80-8cc2-6a8d10c2f305/end -> HTTP 500
```

API requests:

```text
GET /api/profile
GET /api/profile
POST /api/sessions
POST /api/sessions/<id>/end
```

## S27

**Delete all** (Data; mock): PASS

- Does: Opens Profile, taps Delete all, confirms.
- Expected: Profile and history are gone, with empty states. Home says Welcome.
- Observed: Rows left in sessions, messages, feedback, conversations, profile: 0, 0, 0, 0, 0. Empty states shown. Home says Welcome.

Checks:

- ok: all tables empty

API requests:

```text
GET /api/profile
GET /api/conversations
POST /api/conversations
GET /api/conversations
GET /api/conversations/1/messages
POST /api/conversations/1/messages
GET /api/conversations
GET /api/profile
GET /api/history
DELETE /api/history
GET /api/profile
GET /api/history
GET /api/history
GET /api/profile
```

## S28

**Crisis by keyboard only** (Data; mock): PASS

- Does: Tabs to Crisis, presses Enter, then Escape.
- Expected: Panel opens, focus moves in, Escape closes it, focus returns.
- Observed: Enter opened the panel with focus inside. Escape closed it and focus returned to Crisis.

Checks:

- ok: focus moved into the panel
- ok: Escape closed it, focus returned

API requests:

```text
GET /api/profile
```
