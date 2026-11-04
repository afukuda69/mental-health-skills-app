<script setup>
// STOP: four fixed screens from content/skills.js. No model call.
// The Observe step offers an optional note. It is hidden until the user asks
// for it (typing is never required, D3). Like the reframe, the note lives only
// in this component's memory: never sent to the backend or model, never
// stored, and cleared on finish, stop, or leaving. The shared crisis phrase
// list runs on it as the user types; a match opens the crisis panel.
import { ref } from 'vue'
import { matchesCrisisPhrase } from '../content/crisisKeywords.js'
import { SKILLS } from '../content/skills.js'
import StepSequence from './StepSequence.vue'

defineProps({
  entryChoice: { type: String, default: null },
  setupMs: { type: Number, required: true },
  crisisOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['finished', 'stopped', 'crisis'])

const noteOpen = ref(false)
const note = ref('')
let flagged = false

function onInput() {
  const match = matchesCrisisPhrase(note.value)
  if (match && !flagged) emit('crisis')
  flagged = match
}

function clearAll() {
  note.value = ''
  noteOpen.value = false
  flagged = false
}
</script>

<template>
  <StepSequence
    :skill="SKILLS.stop"
    :entry-choice="entryChoice"
    :setup-ms="setupMs"
    :crisis-open="crisisOpen"
    @ended="clearAll"
    @finished="emit('finished', $event)"
    @stopped="emit('stopped')"
  >
    <template #step="{ step }">
      <h2>{{ step.title }}</h2>
      <p class="text">{{ step.text }}</p>
      <template v-if="step.optionalNote">
        <button v-if="!noteOpen" type="button" class="link note-toggle" @click="noteOpen = true">
          Write down what you notice (optional)
        </button>
        <div v-else class="note">
          <label for="stop-note" class="muted hint">Just for you. It isn't saved or sent anywhere, and it clears when you finish.</label>
          <textarea id="stop-note" v-model="note" rows="3" placeholder="What do you notice?" @input="onInput"></textarea>
        </div>
      </template>
    </template>
  </StepSequence>
</template>

<style scoped>
.text {
  margin: 8px 0 0;
  font-size: 1.15rem;
}
.note-toggle {
  margin-top: 14px;
  padding: 4px 0;
}
.note {
  margin-top: 14px;
}
.hint {
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
}
textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  font: inherit;
  color: var(--text);
  resize: vertical;
}
</style>
