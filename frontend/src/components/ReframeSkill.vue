<script setup>
// One-minute cognitive reframe. Typing is optional, never graded, no minimum.
// What the user types lives only in this component's memory:
// - steps 1-2 never leave the component;
// - the step-3 answer is sent once for the model's reflection (design.md
//   section e) and is stored nowhere, by the frontend or the backend;
// - everything is cleared on finish, stop, or leaving.
// The shared crisis phrase list runs on the text as the user types; a match
// opens the crisis panel (which pauses the exercise) without clearing anything.
import { reactive, ref } from 'vue'
import { requestReflection } from '../api.js'
import { matchesCrisisPhrase } from '../content/crisisKeywords.js'
import { SKILLS } from '../content/skills.js'
import StepSequence from './StepSequence.vue'

defineProps({
  entryChoice: { type: String, default: null },
  setupMs: { type: Number, required: true },
  crisisOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['finished', 'stopped', 'crisis'])

const skill = SKILLS.reframe
const texts = reactive(skill.steps.map(() => ''))
const flagged = reactive(skill.steps.map(() => false))
const reflection = ref(null)
const sequence = ref(null)

function onInput(i) {
  const match = matchesCrisisPhrase(texts[i])
  if (match && !flagged[i]) emit('crisis')
  flagged[i] = match
}

function pickChip(i, chip) {
  texts[i] = chip
  onInput(i)
}

async function beforeNext(i) {
  if (!skill.steps[i].reflectOnNext) return
  const answer = texts[i].trim()
  // Nothing typed, or text that matched the crisis list: no request, fallback text.
  if (!answer || matchesCrisisPhrase(answer)) {
    reflection.value = skill.fallback
    return
  }
  const result = await requestReflection(sequence.value.clientId, answer)
  if (result?.crisis) emit('crisis')
  reflection.value = result?.text || skill.fallback
}

function clearAll() {
  texts.fill('')
  flagged.fill(false)
  reflection.value = null
}
</script>

<template>
  <StepSequence
    ref="sequence"
    :skill="skill"
    :entry-choice="entryChoice"
    :setup-ms="setupMs"
    :crisis-open="crisisOpen"
    :before-next="beforeNext"
    @ended="clearAll"
    @finished="emit('finished', $event)"
    @stopped="emit('stopped')"
  >
    <template #step="{ step, index }">
      <template v-if="step.reflection">
        <h2>Another way to see it</h2>
        <p v-if="reflection" class="reflection">{{ reflection }}</p>
        <p v-else class="muted">One moment.</p>
      </template>
      <template v-else>
        <label :for="`reframe-${index}`"><h2>{{ step.prompt }}</h2></label>
        <p class="muted hint">Optional. You can leave this empty.</p>
        <div class="chips">
          <button v-for="c in step.chips" :key="c" type="button" class="chip" @click="pickChip(index, c)">{{ c }}</button>
        </div>
        <textarea
          :id="`reframe-${index}`"
          v-model="texts[index]"
          rows="3"
          maxlength="500"
          placeholder="A few words, if you like"
          @input="onInput(index)"
        ></textarea>
      </template>
    </template>
  </StepSequence>
</template>

<style scoped>
.hint {
  margin: 2px 0 12px;
  font-size: 0.9rem;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.chips .chip {
  padding: 8px 12px;
  cursor: pointer;
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
.reflection {
  margin: 8px 0 0;
  font-size: 1.15rem;
}
</style>
