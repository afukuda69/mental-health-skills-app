<script setup>
// Home. The check-in is chosen by the user only; the app never infers it.
//   Tense       -> paced breathing is featured
//   Overwhelmed -> a contracted Home: one big breathing button, Crisis, "Show everything"
//   Okay / Skip -> the usual skill (breathing on a first visit)
// Every choice can be changed, and Activities always lists every skill.
// Nothing starts until the user taps.
import { computed } from 'vue'
import { APP_NAME, BUTTONS, CHECKIN_LABELS, ENTRY_OPTIONS, ENTRY_PROMPT, FOOTER, SKILLS } from '../content/skills.js'
import { plannedSeconds } from '../timing.js'

const props = defineProps({
  profile: { type: Object, default: null },
  checkin: { type: String, default: null },
  showEverything: { type: Boolean, default: false },
})
const emit = defineEmits(['start', 'checkin', 'navigate', 'crisis', 'show-everything'])

const usual = computed(() => props.profile?.usual_skill ?? null)
const featuredId = computed(() => (props.checkin === 'tense' ? 'breathing' : usual.value ?? 'breathing'))
const featured = computed(() => SKILLS[featuredId.value])
const contracted = computed(() => props.checkin === 'overwhelmed' && !props.showEverything)
const kicker = computed(() => {
  if (props.checkin === 'tense' || props.checkin === 'overwhelmed') return 'Suggested'
  return featuredId.value === usual.value ? 'Your usual' : 'Guided practice'
})
const name = computed(() => props.profile?.display_name)
const others = computed(() => ['breathing', 'stop', 'reframe'].filter((id) => id !== featuredId.value))
</script>

<template>
  <!-- Overwhelmed: as little as possible on screen. -->
  <main v-if="contracted" class="screen contracted">
    <p class="greeting">{{ name ? `Hi, ${name}.` : 'One thing at a time.' }}</p>
    <p class="because">
      Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>
    <button type="button" class="primary big" @click="emit('start', 'breathing')">Start paced breathing</button>
    <button type="button" class="danger-soft" @click="emit('crisis')">Crisis support</button>
    <button type="button" class="link small" @click="emit('show-everything')">Show everything</button>
  </main>

  <main v-else class="screen calm">
    <!-- Part one: a short greeting line, and the optional check-in. -->
    <header class="top">
      <h1 class="greeting">{{ name ? `Hi, ${name}.` : 'Welcome.' }}</h1>
      <span class="app-name">{{ APP_NAME }}</span>
    </header>
    <div v-if="!checkin" class="checkin" role="group" aria-labelledby="entry-prompt">
      <p id="entry-prompt" class="prompt">{{ ENTRY_PROMPT }} <span class="muted">Optional.</span></p>
      <div class="options">
        <button v-for="o in ENTRY_OPTIONS" :key="o.key" type="button" class="opt" @click="emit('checkin', o.key)">{{ o.label }}</button>
      </div>
    </div>
    <p v-else class="because">
      Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>

    <!-- Part two: one large Start area for the suggested skill. -->
    <section class="featured" aria-labelledby="featured-title">
      <div class="deco" aria-hidden="true"></div>
      <p class="kicker">{{ kicker }} · {{ plannedSeconds(featured) }} seconds</p>
      <h2 id="featured-title">{{ featured.label }}</h2>
      <p class="purpose">{{ featured.purpose }}</p>
      <button type="button" class="primary start" :aria-label="`Start ${featured.label}`" @click="emit('start', featured.id)">{{ BUTTONS.start }}</button>
    </section>

    <div class="pills" role="group" aria-label="Other skills">
      <button
        v-for="id in others"
        :key="id"
        type="button"
        class="pill"
        :aria-label="id === usual ? `${BUTTONS.useUsual}: ${SKILLS[id].label}` : `Start ${SKILLS[id].label}`"
        @click="emit('start', id)"
      >
        {{ SKILLS[id].label }}<span v-if="id === usual" class="tag"> · your usual</span>
      </button>
    </div>

    <footer class="disclaimer">{{ FOOTER }}</footer>
  </main>
</template>

<style scoped>
.calm {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--tabbar-h) - var(--tabbar-gap) * 2 - 8px);
}
.top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.greeting {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
}
.app-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent);
}
.checkin {
  margin: 14px 0 0;
}
.prompt {
  margin: 0 0 8px;
  font-weight: 600;
}
.options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.opt {
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--surface);
  color: var(--text);
  font-weight: 500;
  font-size: 0.92rem;
}
.because {
  margin: 12px 0 0;
  color: var(--muted);
}
.because .link {
  padding: 2px 4px;
}
/* One large, quiet Start area. */
.featured {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  margin: 22px 0 16px;
  padding: 28px 22px;
  border-radius: 28px;
  background: var(--tint);
}
.deco {
  width: 150px;
  height: 150px;
  margin-bottom: 18px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, var(--circle-out), var(--circle) 75%);
  border: 2px solid var(--circle-edge);
}
.kicker {
  margin: 0 0 4px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--accent);
}
.featured h2 {
  font-size: 1.8rem;
  margin-bottom: 4px;
}
.purpose {
  max-width: 32ch;
  margin: 0 0 20px;
  color: var(--muted);
}
.start {
  font-size: 1.15rem;
  padding: 18px;
}
.pills {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}
.pill {
  flex: none;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--secondary);
  color: var(--accent);
  font-size: 0.92rem;
}
.tag {
  font-weight: 400;
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
</style>
