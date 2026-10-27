// Pure timing helpers: the breathing schedule and an exercise clock that
// counts active time only (user pauses, hidden-tab time, and crisis-panel
// time are tracked separately). No DOM, so vitest can run them directly.

export function plannedMs(skill) {
  return skill.introMs + skill.cycles * (skill.inMs + skill.outMs)
}

// Where the breathing exercise is, given active ms since the first instruction
// and the active ms at which the intro ended (null while still in the intro).
export function breathingPosition(skill, activeMs, introEndMs) {
  if (introEndMs === null) {
    return { stage: 'intro', cyclesDone: 0 }
  }
  const cycleMs = skill.inMs + skill.outMs
  const b = Math.max(0, activeMs - introEndMs)
  if (b >= skill.cycles * cycleMs) {
    return { stage: 'closing', cyclesDone: skill.cycles }
  }
  const index = Math.floor(b / cycleMs)
  const within = b - index * cycleMs
  const inhale = within < skill.inMs
  const phaseMs = inhale ? skill.inMs : skill.outMs
  const phaseElapsed = inhale ? within : within - skill.inMs
  return {
    stage: 'breathing',
    cycle: index + 1,
    cyclesDone: index,
    phase: inhale ? 'in' : 'out',
    phaseElapsed,
    phaseMs,
    phaseRemainingS: Math.ceil((phaseMs - phaseElapsed) / 1000),
  }
}

// Circle scale for the animated cue: grows 0.6 -> 1 on "In", shrinks on "Out".
export function circleScale(pos) {
  if (pos.stage !== 'breathing') return 0.6
  const t = pos.phaseElapsed / pos.phaseMs
  const eased = 0.5 - Math.cos(Math.PI * t) / 2
  const p = pos.phase === 'in' ? eased : 1 - eased
  return 0.6 + 0.4 * p
}

const PRIORITY = ['crisis', 'user', 'hidden']

export function createExerciseClock(now = () => performance.now()) {
  let activeBefore = 0
  let runningSince = null
  let heldSince = null
  const held = new Set()
  const totals = { crisis: 0, user: 0, hidden: 0 }

  // Time while held goes to the highest-priority reason: crisis, then user, then hidden.
  function closeHeldInterval() {
    if (heldSince === null) return
    const kind = PRIORITY.find((k) => held.has(k))
    totals[kind] += now() - heldSince
    heldSince = now()
  }

  return {
    start() {
      runningSince = now()
    },
    hold(kind) {
      if (held.has(kind)) return
      if (held.size === 0) {
        if (runningSince !== null) activeBefore += now() - runningSince
        runningSince = null
        heldSince = now()
      } else {
        closeHeldInterval()
      }
      held.add(kind)
    },
    release(kind) {
      if (!held.has(kind)) return
      closeHeldInterval()
      held.delete(kind)
      if (held.size === 0) {
        heldSince = null
        runningSince = now()
      }
    },
    isHeld: (kind) => (kind ? held.has(kind) : held.size > 0),
    activeMs() {
      return activeBefore + (runningSince !== null ? now() - runningSince : 0)
    },
    report() {
      closeHeldInterval()
      return {
        measured_ms: Math.round(this.activeMs()),
        pauses_ms: Math.round(totals.user + totals.hidden),
        crisis_ms: Math.round(totals.crisis),
      }
    },
  }
}
