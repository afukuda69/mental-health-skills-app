#!/usr/bin/env bash
# Endpoint checks against a running backend. Fictional data only.
# Usage: API=http://127.0.0.1:8000 bash scripts/api_checks.sh <step>
#   steps: mock | ack (one acknowledgment, for the failure/live modes)
set -u
API="${API:-http://127.0.0.1:8000}/api"
j() { curl -s -X POST "$API$1" -H 'Content-Type: application/json' -d "$2"; echo; }
start() { j /sessions "{\"client_id\":\"$1\",\"skill\":\"${2:-breathing}\",\"entry_choice\":\"${3:-tense}\",\"setup_ms\":6400,\"planned_ms\":75000,\"steps_planned\":7}" > /dev/null; }

case "${1:-mock}" in
  mock)
    echo "## GET /api/health"; curl -s "$API/health"; echo
    echo "## Completed run: start, acknowledgment, end, feedback"
    start demo-complete
    echo "-> acknowledgment:"; j /sessions/demo-complete/acknowledgment ''
    echo "-> end completed:"; j /sessions/demo-complete/end '{"end_reason":"completed","measured_ms":75412,"pauses_ms":0,"crisis_ms":0,"steps_completed":7}' | cut -c1-200
    echo "-> feedback:"; j /sessions/demo-complete/feedback '{"rating":"helped"}'
    echo "## Stop exercise mid-run, then an acknowledgment request (must be refused, no model call)"
    start demo-stopped
    j /sessions/demo-stopped/end '{"end_reason":"stopped","measured_ms":23110,"pauses_ms":0,"crisis_ms":0,"steps_completed":1}' | cut -c1-200
    curl -s -o /dev/null -w "acknowledgment after stop -> HTTP %{http_code}\n" -X POST "$API/sessions/demo-stopped/acknowledgment"
    echo "## Left the page: sendBeacon-style text/plain body"
    start demo-left
    curl -s -X POST "$API/sessions/demo-left/end" -H 'Content-Type: text/plain' -d '{"end_reason":"left","measured_ms":31877,"pauses_ms":0,"crisis_ms":0,"steps_completed":2}' | cut -c1-200; echo
    echo "## Crisis phrase in typed text (fictional): scripted reply, no model call"
    start demo-crisis reframe okay
    j /sessions/demo-crisis/messages '{"text":"Fictional test phrase: I want to die"}'
    echo "## Ordinary typed text (fictional): stored, model reply"
    start demo-text reframe okay
    j /sessions/demo-text/messages '{"text":"Fictional: the presentation might go fine"}'
    echo "## GET /api/usual"; curl -s "$API/usual"; echo
    ;;
  ack)
    id="demo-${2:-ack}"
    start "$id"
    j "/sessions/$id/acknowledgment" ''
    ;;
esac
