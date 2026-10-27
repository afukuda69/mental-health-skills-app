<script setup>
// Entry screen (design.md section c), restyled. The entry choice stays an
// optional one-tap card; it is sent with the session as before. The usual
// skill is a label and a button only: nothing starts until tapped.
import { computed } from 'vue'
import { APP_NAME, BUTTONS, ENTRY_OPTIONS, ENTRY_PROMPT, FOOTER, HOME_HEADLINE, SKILLS } from '../content/skills.js'
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
  <main class="screen">
    <p class="label">{{ APP_NAME }}</p>
    <h1>{{ HOME_HEADLINE }}</h1>

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

    <section class="card sage featured" aria-labelledby="featured-title">
      <div class="featured-top">
        <p class="label">{{ isUsual ? 'Your usual' : 'Guided practice' }}</p>
        <span class="chip"><AppIcon name="clock" :size="16" /> {{ plannedSeconds(skill) }} seconds</span>
      </div>
      <h2 id="featured-title">{{ skill.label }}</h2>
      <p class="purpose">{{ skill.purpose }}</p>
      <div class="deco" aria-hidden="true"><div class="ring"><div class="ball"></div></div></div>
      <button type="button" class="primary" @click="$emit('start', skill.id)">
        {{ isUsual ? `${BUTTONS.useUsual}: ${skill.label}` : BUTTONS.openPractice }} <AppIcon name="arrow" :size="18" />
      </button>
    </section>

    <div class="list history-link">
      <button type="button" class="list-row" @click="$emit('history')">
        <span class="icon-tile blue"><AppIcon name="history" /></span>
        <span><span class="title">History</span><span class="sub">Past practices</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
    </div>

    <footer class="disclaimer">{{ FOOTER }}</footer>
  </main>
</template>

<style scoped>
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
  cursor: pointer;
}
.entry-options .chip.selected {
  background: var(--sage);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.featured {
  position: relative;
  overflow: hidden;
  padding: 22px;
}
.featured-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.featured h2 {
  font-size: 1.9rem;
  max-width: 60%;
}
.purpose {
  max-width: 60%;
  margin: 8px 0 22px;
  color: var(--muted);
}
.featured .primary {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}
/* Static decorative circle: no animation (D6). */
.deco {
  position: absolute;
  right: -24px;
  top: 70px;
}
.ring {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  border: 1px solid var(--sage-strong);
  display: grid;
  place-items: center;
}
.ball {
  width: 104px;
  height: 104px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, var(--circle-out), var(--circle) 70%);
}
.history-link {
  margin-top: 16px;
}
</style>
