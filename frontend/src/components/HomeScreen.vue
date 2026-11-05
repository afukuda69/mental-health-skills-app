<script setup>
// Home: a landing page. Nothing is featured or started until the user acts.
// The check-in is chosen by the user only; the app never infers it.
//   Tense       -> a suggestion card for paced breathing
//   Overwhelmed -> a contracted Home: one big breathing button, Crisis, "Show everything" (D1)
//   Okay        -> a suggestion card for the usual skill (breathing on a first visit)
//   Skip        -> no suggestion; the user picks from Activities
// Every choice can be changed, and Activities always lists every skill (R4).
import { computed } from 'vue'
import { APP_NAME, BUTTONS, CHECKIN_LABELS, ENTRY_OPTIONS, ENTRY_PROMPT, FOOTER, SKILLS } from '../content/skills.js'
import { plannedSeconds } from '../timing.js'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  profile: { type: Object, default: null },
  checkin: { type: String, default: null },
  showEverything: { type: Boolean, default: false },
})
const emit = defineEmits(['start', 'checkin', 'navigate', 'crisis', 'show-everything'])

const usual = computed(() => props.profile?.usual_skill ?? null)
const contracted = computed(() => props.checkin === 'overwhelmed' && !props.showEverything)
const suggestedId = computed(() => {
  if (props.checkin === 'tense' || props.checkin === 'overwhelmed') return 'breathing'
  if (props.checkin === 'okay') return usual.value ?? 'breathing'
  return null // no check-in yet, or Skip: nothing is suggested
})
const suggested = computed(() => (suggestedId.value ? SKILLS[suggestedId.value] : null))
const suggestedIsUsual = computed(() => suggestedId.value && suggestedId.value === usual.value)
const name = computed(() => props.profile?.display_name)

const WAYS = [
  { to: 'activities', icon: 'activities', title: 'Choose a skill', sub: 'Three short skills, about a minute each' },
  { to: 'chat', icon: 'chat', title: 'Talk it through', sub: 'Optional chat about the skills' },
  { to: 'profile', icon: 'profile', title: 'Profile and history', sub: 'What the app has learned, and past sessions' },
]
const PROMISES = [
  { title: 'Nothing starts by itself', text: 'A skill begins only when you tap Start.' },
  { title: 'Stop whenever you like', text: 'One tap, no questions, nothing lost.' },
  { title: 'Support is always one tap away', text: 'The Crisis button stays on every screen.' },
]
</script>

<template>
  <!-- Overwhelmed: as little as possible on screen. -->
  <main v-if="contracted" class="screen contracted">
    <h1 class="greeting">{{ name ? `Hi, ${name}.` : 'One thing at a time.' }}</h1>
    <p class="because">
      Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>
    <button type="button" class="primary big" @click="emit('start', 'breathing')">Start paced breathing</button>
    <button type="button" class="danger-soft" @click="emit('crisis')">Crisis support</button>
    <button type="button" class="link small" @click="emit('show-everything')">Show everything</button>
  </main>

  <main v-else class="screen landing">
    <!-- Welcome -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-text">
        <h1 id="hero-title">{{ APP_NAME }}</h1>
        <h2 class="greeting-line">{{ name ? `Hi, ${name}.` : 'Welcome.' }}</h2>
        <p class="lede">Short guided skills for tense moments. Each one takes about a minute, and you can stop at any time.</p>
        <p class="badge">Coursework prototype · not a support service</p>
      </div>
      <div class="hero-deco" aria-hidden="true">
        <!-- A pale sun rising behind a wave, matching the page background. Static (D6). -->
        <svg viewBox="0 0 120 120" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <g stroke="var(--circle-edge)" stroke-width="2.5" opacity="0.7">
            <path d="M60 22 V14" /><path d="M33 33 L27 27" /><path d="M87 33 L93 27" />
            <path d="M22 60 H14" /><path d="M98 60 H106" />
          </g>
          <circle cx="60" cy="66" r="30" fill="var(--circle-out)" stroke="var(--circle-edge)" stroke-width="2.5" />
          <path d="M10 72 C30 62 46 62 62 72 C78 82 94 82 110 72 L110 110 L10 110 Z" fill="var(--tint)" />
          <path d="M10 72 C30 62 46 62 62 72 C78 82 94 82 110 72" stroke="var(--accent)" stroke-width="3" />
          <path d="M22 90 C38 82 52 82 66 90 C80 98 94 98 104 90" stroke="var(--circle-edge)" stroke-width="2.5" opacity="0.8" />
        </svg>
      </div>
    </section>

    <!-- Optional check-in, or the suggestion it produced -->
    <section v-if="!checkin" class="card checkin" role="group" aria-labelledby="entry-prompt">
      <p id="entry-prompt" class="prompt">{{ ENTRY_PROMPT }} <span class="muted">Optional. It only changes what's suggested.</span></p>
      <div class="options">
        <button v-for="o in ENTRY_OPTIONS" :key="o.key" type="button" class="opt" @click="emit('checkin', o.key)">{{ o.label }}</button>
      </div>
    </section>

    <section v-else-if="suggested" class="card tint suggestion" aria-labelledby="suggestion-title">
      <p class="kicker">{{ suggestedIsUsual ? 'Your usual' : 'Suggested' }} · {{ plannedSeconds(suggested) }} seconds</p>
      <h2 id="suggestion-title">{{ suggested.label }}</h2>
      <p class="purpose">{{ suggested.purpose }}</p>
      <p class="because">
        Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
        <button type="button" class="link" @click="emit('checkin', null)">Change</button>
      </p>
      <button type="button" class="primary start" :aria-label="`Start ${suggested.label}`" @click="emit('start', suggestedId)">{{ BUTTONS.start }}</button>
    </section>

    <p v-else class="because">
      No suggestion. Pick any skill below.
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>

    <!-- Ways to begin -->
    <h2 class="section-title">Ways to begin</h2>
    <div class="ways">
      <button v-for="w in WAYS" :key="w.to" type="button" class="card way" @click="emit('navigate', w.to)">
        <span class="icon-tile"><AppIcon :name="w.icon" /></span>
        <span class="way-text">
          <span class="title">{{ w.title }}</span>
          <span class="sub">{{ w.sub }}</span>
        </span>
        <span class="chevron"><AppIcon name="chevron" :size="18" /></span>
      </button>
    </div>
    <button v-if="usual && suggestedId !== usual" type="button" class="link usual" @click="emit('start', usual)">
      {{ BUTTONS.useUsual }}: {{ SKILLS[usual].label }} →
    </button>

    <!-- How the app treats you -->
    <h2 class="section-title">How this app works</h2>
    <ul class="promises">
      <li v-for="p in PROMISES" :key="p.title">
        <span class="title">{{ p.title }}</span>
        <span class="sub">{{ p.text }}</span>
      </li>
    </ul>

    <footer class="disclaimer">{{ FOOTER }}</footer>
  </main>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 4px 4px;
}
.hero-text {
  flex: 1;
}
/* The app name is the page title; the greeting sits below it. */
.hero h1 {
  margin: 0;
  font-size: 2.4rem;
  font-weight: 800;
  line-height: 1.1;
  color: var(--accent);
}
.greeting-line {
  margin: var(--space-1) 0 var(--space-2);
  font-size: 1.6rem;
  font-weight: 700;
}
.lede {
  margin: 0 0 12px;
  max-width: 46ch;
  color: var(--muted);
  font-size: 1.05rem;
}
.badge {
  display: inline-block;
  margin: 0;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  background: var(--secondary);
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 600;
}
.hero-deco {
  flex: none;
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 40%, var(--surface), var(--tint) 70%);
}
.hero-deco svg {
  width: 72%;
  height: 72%;
}
.checkin,
.suggestion {
  margin-top: 22px;
}
.prompt {
  margin: 0 0 10px;
  font-weight: 600;
}
.options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.opt {
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--secondary);
  color: var(--accent);
  font-weight: 500;
  font-size: 0.95rem;
}
.kicker {
  margin: 0 0 4px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--accent);
}
.purpose {
  margin: 0 0 8px;
  color: var(--muted);
}
.because {
  margin: 14px 0 0;
  color: var(--muted);
}
.suggestion .because {
  margin: 0 0 14px;
}
.because .link {
  padding: 2px 4px;
}
.start {
  max-width: 320px;
}
.section-title {
  margin: 30px 4px 12px;
  font-size: 1.1rem;
}
.ways {
  display: grid;
  gap: 10px;
}
.way {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  text-align: left;
  color: var(--text);
  font-weight: 400;
}
.way-text {
  flex: 1;
}
.title {
  display: block;
  font-weight: 700;
}
.sub {
  display: block;
  font-size: 0.9rem;
  color: var(--muted);
}
.chevron {
  color: var(--muted);
}
.usual {
  margin-top: 10px;
}
.promises {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.promises li {
  padding: 14px 16px;
  border-left: 4px solid var(--circle-edge);
  border-radius: 12px;
  background: var(--surface);
}
.contracted {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 40px;
}
.contracted .greeting {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}
.contracted .because {
  margin: 0;
}
.contracted .big {
  padding: 26px 18px;
  font-size: 1.2rem;
}
.small {
  align-self: center;
  font-size: 0.9rem;
}
@media (min-width: 900px) {
  .hero {
    gap: 48px;
    padding: 12px 4px 8px;
  }
  .hero h1 {
    font-size: 3.5rem;
  }
  .lede {
    font-size: 1.3rem;
    margin-bottom: 18px;
  }
  .badge {
    font-size: 0.95rem;
    padding: 6px 16px;
  }
  .hero-deco {
    width: 220px;
    height: 220px;
  }
  .checkin,
  .suggestion {
    margin-top: 32px;
  }
  .prompt {
    font-size: 1.15rem;
    margin-bottom: 14px;
  }
  .opt {
    padding: 12px 20px;
    font-size: 1.05rem;
  }
  .suggestion h2 {
    font-size: 2rem;
  }
  .section-title {
    margin: 44px 4px 16px;
    font-size: 1.45rem;
  }
  .ways,
  .promises {
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
  }
  .way {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    min-height: 190px;
    padding: 28px;
  }
  .way .title {
    font-size: 1.2rem;
  }
  .way .sub {
    font-size: 1rem;
  }
  .way .chevron {
    margin-top: auto;
  }
  .promises li {
    padding: 22px 24px;
  }
  .promises .title {
    font-size: 1.1rem;
    margin-bottom: 4px;
  }
  .promises .sub {
    font-size: 1rem;
  }
}
</style>
