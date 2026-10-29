<script setup>
// Every skill, always available, as a plain list (three items, not a
// library or dashboard: design D2). A colour stripe marks each skill.
// Suggestions are labels only; nothing starts until tapped (AGENTS.md rule 9).
import { SKILLS } from '../content/skills.js'
import { plannedSeconds } from '../timing.js'
import AppIcon from './AppIcon.vue'

defineProps({ usualSkill: { type: String, default: null } })
defineEmits(['start', 'navigate'])

const ORDER = ['breathing', 'stop', 'reframe']
</script>

<template>
  <main class="screen">
    <h1>Activities</h1>
    <ul class="skills">
      <li v-for="id in ORDER" :key="id" class="skill" :class="id">
        <button type="button" class="row" :aria-label="`Start ${SKILLS[id].label}`" @click="$emit('start', id)">
          <span class="text">
            <span class="name">
              {{ SKILLS[id].label }}
              <span v-if="id === usualSkill" class="usual">Your usual</span>
            </span>
            <span class="purpose">{{ SKILLS[id].purpose }}</span>
            <span class="meta">{{ plannedSeconds(SKILLS[id]) }} seconds · {{ SKILLS[id].effort }}</span>
          </span>
          <AppIcon class="chevron" name="chevron" />
        </button>
      </li>
    </ul>

    <ul class="skills">
      <li class="skill chat">
        <button type="button" class="row" @click="$emit('navigate', 'chat')">
          <span class="text">
            <span class="name">Talk it through</span>
            <span class="purpose">Optional chat. Ask about a skill or explore a fictional scenario.</span>
          </span>
          <AppIcon class="chevron" name="chevron" />
        </button>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.skills {
  list-style: none;
  margin: 0 0 20px;
  padding: 0;
  background: var(--surface);
  border-radius: 14px;
  overflow: hidden;
}
.skill + .skill {
  border-top: 1px solid var(--line);
}
/* The stripe: a 6 px coloured edge on the left of each row. */
.skill {
  border-left: 6px solid var(--line);
}
.skill.breathing {
  border-left-color: var(--skill-breathing);
}
.skill.stop {
  border-left-color: var(--skill-stop);
}
.skill.reframe {
  border-left-color: var(--skill-reframe);
}
.skill.chat {
  border-left-color: var(--secondary);
}
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 16px;
  border-radius: 0;
  background: none;
  color: var(--text);
  text-align: left;
  font-weight: 400;
}
.text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.name {
  font-weight: 700;
  font-size: 1.05rem;
}
.usual {
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--secondary);
  color: var(--accent);
  font-size: 0.8rem;
  font-weight: 600;
}
.purpose {
  color: var(--muted);
  font-size: 0.92rem;
}
.meta {
  color: var(--muted);
  font-size: 0.85rem;
}
.chevron {
  margin-left: auto;
  flex: none;
  color: var(--muted);
}
</style>
