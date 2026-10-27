<script setup>
// Lists only skills marked available in content/skills.js. The usual skill
// is labelled, never preselected or started automatically (AGENTS.md rule 9).
import { availableSkills } from '../content/skills.js'

defineProps({ usualSkill: { type: String, default: null } })
defineEmits(['pick', 'back'])
</script>

<template>
  <main class="screen">
    <h1>Choose a skill</h1>
    <div class="options">
      <button v-for="s in availableSkills()" :key="s.id" type="button" @click="$emit('pick', s.id)">
        {{ s.label }}
        <span v-if="s.id === usualSkill" class="tag">Your usual</span>
      </button>
    </div>
    <button type="button" class="link back" @click="$emit('back')">Back</button>
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
.tag {
  display: block;
  font-size: 0.85rem;
  color: var(--muted);
}
.back {
  margin-top: 32px;
}
</style>
