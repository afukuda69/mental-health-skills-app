<script setup>
// STOP: four fixed screens from content/skills.js. No model call.
import { SKILLS } from '../content/skills.js'
import StepSequence from './StepSequence.vue'

defineProps({
  entryChoice: { type: String, default: null },
  setupMs: { type: Number, required: true },
  crisisOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['finished', 'stopped'])
</script>

<template>
  <StepSequence
    :skill="SKILLS.stop"
    :entry-choice="entryChoice"
    :setup-ms="setupMs"
    :crisis-open="crisisOpen"
    @finished="emit('finished', $event)"
    @stopped="emit('stopped')"
  >
    <template #step="{ step }">
      <h2>{{ step.title }}</h2>
      <p class="text">{{ step.text }}</p>
    </template>
  </StepSequence>
</template>

<style scoped>
.text {
  margin: 8px 0 0;
  font-size: 1.15rem;
}
</style>
