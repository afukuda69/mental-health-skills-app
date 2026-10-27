<script setup>
// Entry screen (design.md section c), restyled. The entry choice stays an
// optional one-tap card; it is sent with the session as before. The usual
// skill is a label and a link only: nothing starts until tapped.
import { computed } from 'vue'
import { APP_NAME, BUTTONS, ENTRY_OPTIONS, ENTRY_PROMPT, FOOTER, SKILLS } from '../content/skills.js'
import { plannedSeconds } from '../timing.js'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  usualSkill: { type: String, default: null },
  entryChoice: { type: String, default: null },
})
defineEmits(['start', 'choose', 'history'])

const skill = SKILLS.breathing
const isUsual = computed(() => props.usualSkill === skill.id)
</script>

<template>
  <header class="topbar">
    <h1 class="app-name">{{ APP_NAME }}</h1>
  </header>
  <main class="screen">
    <section class="card entry" aria-labelledby="entry-prompt">
      <p id="entry-prompt" class="entry-title">{{ ENTRY_PROMPT }}</p>
      <p class="entry-sub">Optional. One tap, then open the practice.</p>
      <div class="entry-options">
        <button
          v-for="o in ENTRY_OPTIONS"
          :key="o.key"
          type="button"
          class="chip"
          :class="{ selected: entryChoice === o.key }"
          :aria-pressed="entryChoice === o.key"
          @click="$emit('choose', entryChoice === o.key ? null : o.key)"
        >
          {{ o.label }}
        </button>
      </div>
    </section>

    <section class="card tint featured" aria-labelledby="featured-title">
      <!-- Static decorative circle: no animation (D6). -->
      <div class="deco" aria-hidden="true"><div class="ball"></div></div>
      <p class="kicker">{{ isUsual ? 'Your usual' : 'Guided practice' }}</p>
      <h2 id="featured-title">{{ skill.label }}</h2>
      <p class="purpose">{{ skill.purpose }}</p>
      <span class="chip duration"><AppIcon name="clock" :size="16" /> {{ plannedSeconds(skill) }} seconds</span>
      <button type="button" class="primary" @click="$emit('start', skill.id)">{{ BUTTONS.openPractice }}</button>
      <button v-if="isUsual" type="button" class="link usual" @click="$emit('start', skill.id)">
        {{ BUTTONS.useUsual }}: {{ skill.label }}
      </button>
    </section>

    <div class="list history-link">
      <button type="button" class="list-row" @click="$emit('history')">
        <span class="icon-tile"><AppIcon name="history" /></span>
        <span><span class="title">History</span><span class="sub">Past practices</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
    </div>

    <footer class="disclaimer">{{ FOOTER }}</footer>
  </main>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  padding: 16px 20px 0;
}
.app-name {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--accent);
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
  background: var(--surface);
  font-weight: 500;
}
.entry-options .chip.selected {
  background: var(--secondary);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
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
.history-link {
  margin-top: 16px;
}
</style>
