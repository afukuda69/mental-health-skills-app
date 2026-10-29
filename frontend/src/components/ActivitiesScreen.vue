<script setup>
// One card per skill (not a library or dashboard: three items, design D2).
// Suggestions are labels only; nothing starts until tapped (AGENTS.md rule 9).
import { SKILLS } from '../content/skills.js'
import { plannedSeconds } from '../timing.js'
import AppIcon from './AppIcon.vue'

defineProps({ usualSkill: { type: String, default: null } })
defineEmits(['start', 'navigate'])

const ICONS = { breathing: ['breath', 'sage'], stop: ['pause', 'pink'], reframe: ['spark', 'blue'] }
const ORDER = ['breathing', 'stop', 'reframe']
</script>

<template>
  <main class="screen">
    <h1>Activities</h1>
    <p class="section-label">Skills</p>
    <div class="cards">
      <article v-for="id in ORDER" :key="id" class="card skill" :class="{ tint: id === usualSkill }">
        <div class="top">
          <span class="icon-tile" :class="ICONS[id][1]"><AppIcon :name="ICONS[id][0]" /></span>
          <span class="chip"><AppIcon name="clock" :size="16" /> {{ plannedSeconds(SKILLS[id]) }} seconds</span>
        </div>
        <h2>{{ SKILLS[id].label }}</h2>
        <p class="muted purpose">{{ SKILLS[id].purpose }}</p>
        <p class="effort">
          {{ SKILLS[id].effort }}<span v-if="id === usualSkill"> · Your usual</span>
        </p>
        <button
          v-if="SKILLS[id].available"
          type="button"
          class="primary"
          :aria-label="`Start ${SKILLS[id].label}`"
          @click="$emit('start', id)"
        >
          Start
        </button>
        <p v-else class="muted">Not available yet.</p>
      </article>
    </div>

    <p class="section-label">Optional chat</p>
    <div class="list">
      <button type="button" class="list-row" @click="$emit('navigate', 'chat')">
        <span class="icon-tile pink"><AppIcon name="chat" /></span>
        <span><span class="title">Talk it through · optional chat</span><span class="sub">Ask about a skill or explore a fictional scenario.</span></span>
        <AppIcon class="chevron" name="chevron" />
      </button>
    </div>
  </main>
</template>

<style scoped>
.cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.purpose {
  margin: 4px 0 6px;
}
.effort {
  margin: 0 0 14px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
}
</style>
