<script setup>
import { ENTRY_OPTIONS, ENTRY_PROMPT, FOOTER, SKILLS } from '../content/skills.js'

defineProps({ usualSkill: { type: String, default: null } })
defineEmits(['choose', 'use-usual', 'history'])
</script>

<template>
  <main class="screen">
    <h1>{{ ENTRY_PROMPT }}</h1>
    <div class="options">
      <button v-for="o in ENTRY_OPTIONS" :key="o.key" type="button" @click="$emit('choose', o.key)">
        {{ o.label }}
      </button>
    </div>
    <button
      v-if="usualSkill && SKILLS[usualSkill]?.available"
      type="button"
      class="primary usual"
      @click="$emit('use-usual')"
    >
      Use my usual: {{ SKILLS[usualSkill].label }}
    </button>
    <footer>
      <button type="button" class="link" @click="$emit('history')">History</button>
      <p>{{ FOOTER }}</p>
    </footer>
  </main>
</template>

<style scoped>
.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 320px;
}
.usual {
  margin-top: 28px;
  width: 100%;
  max-width: 320px;
}
footer {
  margin-top: 48px;
  color: var(--muted);
  font-size: 0.9rem;
}
</style>
