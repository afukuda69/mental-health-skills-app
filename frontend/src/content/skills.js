// All skill step text and timings live here (AGENTS.md rule 3).
// The model never writes or changes anything in this file.
// Fallback strings must match backend/model_client.py FALLBACKS.

export const APP_NAME = 'Short skills'
export const HOME_HEADLINE = 'One short skill at a time.'

export const ENTRY_PROMPT = 'How are you right now?'

export const ENTRY_OPTIONS = [
  { key: 'tense', label: 'Tense or wound up' },
  { key: 'overwhelmed', label: 'Overwhelmed' },
  { key: 'okay', label: 'Okay, just want a minute' },
]

export const SKILLS = {
  breathing: {
    id: 'breathing',
    label: 'Paced breathing',
    purpose: 'Breathe in for 4 seconds and out for 6, seven times, following a circle.',
    available: true,
    component: 'BreathingSkill',
    intro: 'Breathe in as the circle grows, out as it shrinks. Seven slow breaths.',
    introMs: 5000,
    cycles: 7,
    inMs: 4000,
    outMs: 6000,
    inLabel: 'Breathe in',
    outLabel: 'Breathe out',
    fallback: 'That was seven slow breaths.',
  },
  // Part 3.3: STOP and the one-minute reframe get their step text here and
  // their own component; nothing else in the flow needs to change.
  stop: { id: 'stop', label: 'STOP', available: false },
  reframe: { id: 'reframe', label: 'One-minute reframe', available: false },
}

export const availableSkills = () => Object.values(SKILLS).filter((s) => s.available)

export const BUTTONS = {
  start: 'Start',
  continue: 'Continue',
  pause: 'Pause',
  resume: 'Resume',
  stopExercise: 'Stop exercise',
  backToStart: 'Back to start',
  openPractice: 'Open practice',
  useUsual: 'Use my usual',
  close: 'Close',
}

export const CHECK_IN = {
  prompt: 'Did this help?',
  options: [
    { key: 'helped', label: 'Helped' },
    { key: 'didnt_help', label: "Didn't help" },
    { key: null, label: 'Skip' },
  ],
}

export const DONE = {
  finished: 'Done.',
  stopped: "Stopped. That's fine.",
  closeHint: 'You can close this tab now.',
}

export const FOOTER = 'Coursework prototype. Not a support service. Nobody monitors this app.'
