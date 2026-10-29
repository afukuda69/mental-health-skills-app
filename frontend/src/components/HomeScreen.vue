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
import AppIcon from './AppIcon.vue'

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
</script>

<template>
  <header class="topbar">
    <p class="app-name">{{ APP_NAME }}</p>
  </header>

  <!-- Overwhelmed: as little as possible on screen. -->
  <main v-if="contracted" class="screen contracted">
    <h1>{{ name ? `Hi, ${name}.` : 'One thing at a time.' }}</h1>
    <p class="because">
      Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>
    <button type="button" class="primary big" @click="emit('start', 'breathing')">Start paced breathing</button>
    <button type="button" class="danger-soft" @click="emit('crisis')">Crisis support</button>
    <button type="button" class="link small" @click="emit('show-everything')">Show everything</button>
  </main>

  <main v-else class="screen">
    <h1 class="greeting">{{ name ? `Hi, ${name}.` : 'Welcome.' }}</h1>

    <section v-if="!checkin" class="card entry" aria-labelledby="entry-prompt">
      <p id="entry-prompt" class="entry-title">{{ ENTRY_PROMPT }}</p>
      <p class="entry-sub">Optional. Your choice changes what is suggested; nothing starts by itself.</p>
      <div class="entry-options">
        <button v-for="o in ENTRY_OPTIONS" :key="o.key" type="button" class="chip" @click="emit('checkin', o.key)">
          {{ o.label }}
        </button>
      </div>
    </section>
    <p v-else class="because">
      Suggested because you chose "{{ CHECKIN_LABELS[checkin] }}".
      <button type="button" class="link" @click="emit('checkin', null)">Change</button>
    </p>

    <section class="card tint featured" aria-labelledby="featured-title">
      <!-- Static decorative circle: no animation (D6). -->
      <div class="deco" aria-hidden="true"><div class="ball"></div></div>
      <p class="kicker">{{ kicker }}</p>
      <h2 id="featured-title">{{ featured.label }}</h2>
      <p class="purpose">{{ featured.purpose }}</p>
      <span class="chip duration"><AppIcon name="clock" :size="16" /> {{ plannedSeconds(featured) }} seconds</span>
      <button type="button" class="primary" @click="emit('start', featured.id)">{{ BUTTONS.openPractice }}</button>
      <button v-if="usual && usual !== featuredId" type="button" class="link usual" @click="emit('start', usual)">
        {{ BUTTONS.useUsual }}: {{ SKILLS[usual].label }}
      </button>
    </section>

    <p class="section-label">More</p>
    <div class="list">
      <button type="button" class="list-row" @click="emit('navigate', 'activities')">
        <span class="icon-tile"><AppIcon name="activities" /></span>
        <span><span class="title">All activities</span><span class="sub">Every skill, always available</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
      <button type="button" class="list-row" @click="emit('navigate', 'chat')">
        <span class="icon-tile"><AppIcon name="chat" /></span>
        <span><span class="title">Talk it through</span><span class="sub">Optional chat about a skill</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
      <button type="button" class="list-row" @click="emit('navigate', 'profile')">
        <span class="icon-tile"><AppIcon name="profile" /></span>
        <span><span class="title">Profile and history</span><span class="sub">What the app remembers, and how to change it</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
    </div>

    <footer class="disclaimer">{{ FOOTER }}</footer>
  </main>
</template>

<style scoped>
.topbar {
  padding: 16px 20px 0;
}
.app-name {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--accent);
}
.greeting {
  font-size: 1.5rem;
  margin-bottom: 14px;
}
.entry {
  margin-bottom: 16px;
}
.entry-title {
  margin: 0;
  font-weight: 700;
}
.entry-sub {
  margin: 2px 0 12px;
  font-size: 0.9rem;
  color: var(--muted);
}
.entry-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.entry-options .chip {
  padding: 8px 12px;
  color: var(--text);
  font-weight: 500;
}
.because {
  margin: 0 0 14px;
  color: var(--muted);
}
.because .link {
  padding: 2px 4px;
}
.featured {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px 22px 18px;
}
.deco {
  width: 128px;
  height: 128px;
  border-radius: 50%;
  border: 1px solid var(--secondary);
  display: grid;
  place-items: center;
  margin-bottom: 14px;
}
.ball {
  width: 92px;
  height: 92px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, var(--circle-out), var(--circle) 75%);
  border: 2px solid var(--circle-edge);
}
.kicker {
  margin: 0 0 2px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--accent);
}
.purpose {
  margin: 4px 0 12px;
  color: var(--muted);
}
.duration {
  margin-bottom: 16px;
}
.usual {
  margin-top: 8px;
}
.contracted {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 40px;
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
