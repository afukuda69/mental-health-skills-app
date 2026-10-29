<script setup>
// One step per screen for STOP and the reframe (design.md section c): step
// dots, Pause, Next, and a one-tap Stop. Steps advance only when the user taps
// Next (design.md: no auto-advance), and Next works after 2 s on a step.
// Timing and session writes are shared with breathing (useExerciseSession).
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { BUTTONS } from '../content/skills.js'
import { useExerciseSession } from '../composables/useExerciseSession.js'
import { MIN_STEP_MS, plannedMs } from '../timing.js'
import ExerciseFrame from './ExerciseFrame.vue'

const props = defineProps({
  skill: { type: Object, required: true },
  entryChoice: { type: String, default: null },
  setupMs: { type: Number, required: true },
  crisisOpen: { type: Boolean, default: false },
  // Called before leaving step `index`; may start work for the next step.
  beforeNext: { type: Function, default: null },
})
const emit = defineEmits(['finished', 'stopped', 'ended'])

const index = ref(0)
const paused = ref(false)
const activeNow = ref(0)
let stepShownAt = 0
let timer = null

const session = useExerciseSession({
  skill: props.skill,
  entryChoice: props.entryChoice,
  setupMs: props.setupMs,
  plannedMs: plannedMs(props.skill),
  stepsPlanned: props.skill.steps.length,
  crisisOpen: () => props.crisisOpen,
  onHidden: () => {
    paused.value = true
  },
})
const { clock } = session

const steps = props.skill.steps
const isLast = computed(() => index.value === steps.length - 1)
const canNext = computed(() => activeNow.value - stepShownAt >= MIN_STEP_MS)

function next() {
  if (!canNext.value || session.ended.value) return
  props.beforeNext?.(index.value)
  if (isLast.value) {
    session.setStepsCompleted(steps.length)
    // Final planned step finished: the user tapped Finish on it.
    session.end('completed')
    emit('ended')
    emit('finished', session.clientId)
    return
  }
  index.value += 1
  session.setStepsCompleted(index.value)
  stepShownAt = clock.activeMs()
}

function togglePause() {
  if (paused.value) {
    clock.release('hidden')
    clock.release('user')
    paused.value = false
  } else {
    clock.hold('user')
    paused.value = true
  }
}

// Same exit as breathing: one tap, no dialog, then "Stopped. That's fine."
function stop() {
  session.end('stopped')
  emit('ended')
  emit('stopped')
}

onMounted(() => {
  session.begin()
  timer = setInterval(() => (activeNow.value = clock.activeMs()), 200)
})
onUnmounted(() => {
  clearInterval(timer)
  emit('ended')
})

defineExpose({ index, clientId: session.clientId })
</script>

<template>
  <ExerciseFrame :title="skill.label">
    <div>
      <ol class="dots" :aria-label="`Step ${index + 1} of ${steps.length}`">
        <li v-for="(s, i) in steps" :key="i" :class="{ done: i < index, current: i === index }"></li>
      </ol>
      <section class="card step" aria-live="polite">
        <slot name="step" :step="steps[index]" :index="index" :paused="paused" />
      </section>
      <div class="controls">
        <button type="button" class="primary" :disabled="!canNext" @click="next">
          {{ isLast ? BUTTONS.finish : BUTTONS.next }}
        </button>
        <div class="row">
          <button type="button" @click="togglePause">{{ paused ? BUTTONS.resume : BUTTONS.pause }}</button>
          <button type="button" class="danger-soft" @click="stop">{{ BUTTONS.stopExercise }}</button>
        </div>
      </div>
      <p class="notes muted small">
        Stop is always available. Opening Crisis pauses the timer.<br />
        Sessions save when you stop, finish, or leave this screen. Paused time is excluded.
      </p>
    </div>
  </ExerciseFrame>
</template>

<style scoped>
.dots {
  display: flex;
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
}
.dots li {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid var(--circle-edge);
  background: var(--surface);
}
.dots li.done {
  background: var(--circle-edge);
}
.dots li.current {
  background: var(--accent);
  border-color: var(--accent);
}
.step {
  min-height: 180px;
  padding: 22px;
}
.controls {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}
.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.state {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: center;
}
.state h2 {
  margin: 0;
}
.small {
  font-size: 0.85rem;
  margin: 0;
}
.notes {
  margin-top: 14px;
  text-align: center;
}
</style>
