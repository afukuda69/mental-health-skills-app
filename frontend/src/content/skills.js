// All skill step text and timings live here (AGENTS.md rule 3).
// The model never writes or changes anything in this file.
// Fallback strings must match backend/model_client.py FALLBACKS.
// Labels, purpose lines, and effort notes come from shared/skills.json,
// which the backend also reads for the chat context.
import shared from '../../../shared/skills.json'

const meta = Object.fromEntries(shared.skills.map((s) => [s.id, s]))

export const APP_NAME = 'Short skills'

export const ENTRY_PROMPT = 'How are you right now?'

export const ENTRY_OPTIONS = [
  { key: 'tense', label: 'Tense or wound up' },
  { key: 'overwhelmed', label: 'Overwhelmed' },
  { key: 'okay', label: 'Okay, just want a minute' },
  { key: 'skip', label: 'Skip' },
]

export const CHECKIN_LABELS = Object.fromEntries(ENTRY_OPTIONS.map((o) => [o.key, o.label]))

export const SKILLS = {
  breathing: {
    ...meta.breathing,
    available: true,
    kind: 'breathing',
    component: 'BreathingSkill',
    subtitle: 'Seven slow breaths. Stop whenever you like.',
    intro: 'Breathe in as the circle grows, out as it shrinks. Seven slow breaths.',
    introMs: 5000,
    cycles: 7,
    inMs: 4000,
    outMs: 6000,
    inLabel: 'Breathe in',
    outLabel: 'Breathe out',
    fallback: 'That was seven slow breaths.',
  },
  stop: {
    ...meta.stop,
    subtitle: 'Four short steps. Stop whenever you like.',
    available: true,
    kind: 'steps',
    // design.md section c: each screen advances on Next, no auto-advance.
    // stepMs is the planning budget per screen (design.md section d), not a timer.
    steps: [
      { title: 'Stop.', text: "Pause what you're doing for a moment.", stepMs: 15000 },
      { title: 'Take a step back.', text: 'Let yourself take one slow breath.', stepMs: 15000 },
      { title: 'Observe.', text: 'Notice what is happening inside you and around you. Writing it down is optional.', optionalNote: true, stepMs: 15000 },
      { title: 'Proceed mindfully.', text: "Choose what you'll do next.", stepMs: 15000 },
    ],
  },
  reframe: {
    ...meta.reframe,
    subtitle: 'Three short prompts. Typing is optional.',
    available: true,
    kind: 'steps',
    steps: [
      { prompt: "What's the thought?", chips: ['Something will go wrong', 'I messed up', "I'd rather not say"], input: true, stepMs: 20000 },
      { prompt: 'What supports that thought?', chips: ['Something that happened', 'A feeling more than a fact', 'Not sure'], input: true, stepMs: 20000 },
      { prompt: 'Is there another way to see it?', chips: ['It may not be as certain as it feels', "I've got through hard moments before", 'Not sure yet'], input: true, reflectOnNext: true, stepMs: 20000 },
      // Reflection: up to 5 s for the model plus about 5 s to read.
      { reflection: true, stepMs: 10000 },
    ],
    fallback: "You've noted another way to look at it.",
  },
}

export const availableSkills = () => Object.values(SKILLS).filter((s) => s.available)

export const BUTTONS = {
  start: 'Start',
  continue: 'Continue',
  pause: 'Pause',
  resume: 'Resume',
  stopExercise: 'Stop exercise',
  backToStart: 'Back to start',
  next: 'Next',
  finish: 'Finish',
  openPractice: 'Open practice',
  useUsual: 'Use my usual',
  close: 'Close',
}

export const CHECK_IN = {
  prompt: 'Did this help?',
  note: 'One tap. It helps the app learn your usual skill.',
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
  note: 'You can go back to the start, or close this tab.',
}

export const FOOTER = 'Coursework prototype. Not a support service. Nobody monitors this app.'
