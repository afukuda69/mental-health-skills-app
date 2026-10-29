// Session bookkeeping shared by every skill component: the exercise clock,
// the session record, crisis-panel pausing, and recording "left" when the
// page is hidden or closed, or the user navigates away mid-exercise.
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { beacon, send } from '../api.js'
import { createExerciseClock } from '../timing.js'

export function useExerciseSession({ skill, entryChoice, setupMs, plannedMs, stepsPlanned, crisisOpen, onHidden }) {
  const clientId = crypto.randomUUID()
  const clock = createExerciseClock()
  const ended = ref(false)
  let begun = false
  let stepsDone = 0

  // Opening the crisis panel pauses the exercise; closing resumes it at the same point.
  if (crisisOpen) watch(crisisOpen, (open) => (open ? clock.hold('crisis') : clock.release('crisis')))

  function begin() {
    begun = true
    clock.start()
    console.log(`[timing] setup_ms=${Math.round(setupMs)} (entry and skill pick, reported separately)`)
    send('/sessions', {
      client_id: clientId,
      skill: skill.id,
      entry_choice: entryChoice,
      setup_ms: Math.round(setupMs),
      planned_ms: plannedMs,
      steps_planned: stepsPlanned,
      started_at: new Date().toISOString(),
    })
  }

  function setStepsCompleted(n) {
    stepsDone = n
  }

  function end(reason) {
    if (ended.value) return null
    ended.value = true
    const r = clock.report()
    console.log(
      `[timing] exercise measured_ms=${r.measured_ms} pauses_ms=${r.pauses_ms} crisis_ms=${r.crisis_ms} planned_ms=${plannedMs} end_reason=${reason}`,
    )
    send(`/sessions/${clientId}/end`, { end_reason: reason, steps_completed: stepsDone, ...r })
    return r
  }

  // Fires on tab switch as well as close. The backend never lets "left"
  // overwrite "completed" or "stopped", and returning to the tab finds the
  // exercise paused at the same point.
  function onPageHidden() {
    if (ended.value) return
    clock.hold('hidden')
    onHidden?.()
    const r = clock.report()
    beacon(`/sessions/${clientId}/end`, { end_reason: 'left', steps_completed: stepsDone, ...r })
  }
  function onVisibility() {
    if (document.visibilityState === 'hidden') onPageHidden()
  }

  onMounted(() => {
    window.addEventListener('pagehide', onPageHidden)
    document.addEventListener('visibilitychange', onVisibility)
  })
  onUnmounted(() => {
    window.removeEventListener('pagehide', onPageHidden)
    document.removeEventListener('visibilitychange', onVisibility)
    // Navigating to another tab or back to Activities mid-exercise is leaving.
    if (begun && !ended.value) end('left')
  })

  return { clientId, clock, ended, begin, end, setStepsCompleted }
}
