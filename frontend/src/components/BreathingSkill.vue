<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { requestAcknowledgment } from '../api.js'
import { BUTTONS, SKILLS } from '../content/skills.js'
import { useExerciseSession } from '../composables/useExerciseSession.js'
import { breathingPosition, circleScale, plannedMs } from '../timing.js'
import ExerciseFrame from './ExerciseFrame.vue'

const props = defineProps({
  entryChoice: { type: String, default: null },
  setupMs: { type: Number, required: true },
  crisisOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['finished', 'stopped'])

const skill = SKILLS.breathing
const PLANNED_MS = plannedMs(skill)

const paused = ref(false)
const introEnd = ref(null)
const pos = ref(breathingPosition(skill, 0, null))
const closingText = ref(null)
// "Animate circle" is a user control that starts from prefers-reduced-motion.
// With it off the circle stays still and the "Breathe in / Breathe out" label
// carries the pace. No seconds countdown (D6: a ticking number reads as demand).
const animate = ref(true)

const session = useExerciseSession({
  skill,
  entryChoice: props.entryChoice,
  setupMs: props.setupMs,
  plannedMs: PLANNED_MS,
  stepsPlanned: skill.cycles,
  onHidden: () => {
    paused.value = true
  },
})
const { clock } = session

let ackPromise = null
let frame = null

function tick() {
  const active = clock.activeMs()
  if (introEnd.value === null && active >= skill.introMs) introEnd.value = skill.introMs
  pos.value = breathingPosition(skill, active, introEnd.value)
  session.setStepsCompleted(pos.value.cyclesDone)

  // Ask for the acknowledgment at the start of the last cycle so it is
  // usually back before the closing step. The timer never waits for it.
  if (!ackPromise && pos.value.stage === 'breathing' && pos.value.cycle === skill.cycles) {
    ackPromise = requestAcknowledgment(session.clientId)
  }
  if (pos.value.stage === 'closing') {
    showClosing()
    return
  }
  frame = requestAnimationFrame(tick)
}

async function showClosing() {
  const ack = await (ackPromise ?? requestAcknowledgment(session.clientId))
  if (session.ended.value) return
  closingText.value = ack?.text || skill.fallback
  if (!ack) console.warn('[model] acknowledgment unavailable: showing fixed fallback')
  else console.log(`[model] acknowledgment status=${ack.status} latency_ms=${ack.latency_ms}`)
  // Final planned step reached: the closing text is on screen.
  session.end('completed')
}

function startNow() {
  if (introEnd.value === null) introEnd.value = clock.activeMs()
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

function stop() {
  cancelAnimationFrame(frame)
  session.end('stopped')
  emit('stopped')
}

watch(
  () => props.crisisOpen,
  (open) => (open ? clock.hold('crisis') : clock.release('crisis')),
)

onMounted(() => {
  animate.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  session.begin()
  frame = requestAnimationFrame(tick)
})
onUnmounted(() => cancelAnimationFrame(frame))

const phaseLabel = computed(() => (pos.value.phase === 'in' ? skill.inLabel : skill.outLabel))
const circleStyle = computed(() =>
  animate.value && pos.value.stage === 'breathing' ? { transform: `scale(${circleScale(pos.value).toFixed(4)})` } : {},
)
</script>

<template>
  <ExerciseFrame :title="skill.label">
    <div class="circle-area">
      <div class="ring">
        <div class="circle" :class="{ still: !animate, out: !animate && pos.phase === 'out' }" :style="circleStyle"></div>
      </div>
    </div>

    <section v-if="pos.stage === 'intro'" class="state">
      <p class="instruction">{{ skill.intro }}</p>
      <div class="tiles">
        <div class="card tile"><span class="muted small">{{ skill.inLabel }}</span><strong>4</strong><span class="muted small">seconds</span></div>
        <div class="card tile"><span class="muted small">{{ skill.outLabel }}</span><strong>6</strong><span class="muted small">seconds</span></div>
      </div>
      <button type="button" class="primary" @click="startNow">{{ BUTTONS.start }}</button>
      <button type="button" class="danger-soft" @click="stop">{{ BUTTONS.stopExercise }}</button>
    </section>

    <section v-else-if="pos.stage === 'breathing'" class="state" aria-live="polite">
      <h2>{{ phaseLabel }}</h2>
      <p class="muted">Cycle {{ pos.cycle }} of {{ skill.cycles }}</p>
      <button type="button" class="danger-soft" @click="stop">{{ BUTTONS.stopExercise }}</button>
      <button type="button" @click="togglePause">{{ paused ? BUTTONS.resume : BUTTONS.pause }}</button>
    </section>

    <section v-else class="state" aria-live="polite">
      <p v-if="closingText" class="instruction">{{ closingText }}</p>
      <button v-if="closingText" type="button" class="primary" @click="emit('finished', session.clientId)">
        {{ BUTTONS.continue }}
      </button>
      <button type="button" class="danger-soft" @click="stop">{{ BUTTONS.stopExercise }}</button>
    </section>

    <label class="card toggle">
      <span>Animate circle</span>
      <input v-model="animate" type="checkbox" role="switch" />
    </label>
    <p class="notes muted small">
      Stop exercise is always available. Opening Crisis pauses the timer.<br />
      Sessions save when you stop, finish, or leave this page. Paused time is excluded.
    </p>
  </ExerciseFrame>
</template>

<style scoped>
.circle-area {
  display: flex;
  justify-content: center;
  margin: 4px 0 18px;
}
.ring {
  width: 240px;
  height: 240px;
  border-radius: 50%;
  border: 1px solid var(--sage-strong);
  display: grid;
  place-items: center;
}
.circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, var(--circle-out), var(--circle) 70%);
  border: 2px solid var(--circle-edge);
  will-change: transform;
}
/* Animation off: a still circle; the label changes, the fill shifts slightly on "Breathe out". */
.circle.still.out {
  background: var(--circle-out);
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
.instruction {
  margin: 0 0 6px;
  font-size: 1.15rem;
}
.tiles {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
}
.tile strong {
  font-size: 1.6rem;
  line-height: 1.2;
}
.small {
  font-size: 0.85rem;
  margin: 0;
}
.toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 14px 18px;
}
.toggle input {
  width: 22px;
  height: 22px;
  accent-color: var(--accent);
}
.notes {
  margin-top: 14px;
  text-align: center;
}
</style>
