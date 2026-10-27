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
const reducedMotion = ref(false)

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

let motionQuery = null
const onMotionChange = (e) => (reducedMotion.value = e.matches)

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = motionQuery.matches
  motionQuery.addEventListener('change', onMotionChange)
  session.begin()
  frame = requestAnimationFrame(tick)
})
onUnmounted(() => {
  cancelAnimationFrame(frame)
  motionQuery?.removeEventListener('change', onMotionChange)
})

const phaseLabel = computed(() => (pos.value.phase === 'in' ? skill.inLabel : skill.outLabel))
const circleStyle = computed(() =>
  reducedMotion.value ? {} : { transform: `scale(${circleScale(pos.value).toFixed(4)})` },
)
</script>

<template>
  <ExerciseFrame @stop="stop">
    <template v-if="pos.stage === 'intro'">
      <p class="instruction">{{ skill.intro }}</p>
      <button type="button" class="primary" @click="startNow">{{ BUTTONS.start }}</button>
    </template>

    <template v-else-if="pos.stage === 'breathing'">
      <div class="circle-area" aria-live="polite">
        <div class="circle" :class="{ still: reducedMotion, out: pos.phase === 'out' }" :style="circleStyle">
          <span class="phase">{{ phaseLabel }}</span>
          <span v-if="reducedMotion" class="seconds">{{ pos.phaseRemainingS }}</span>
        </div>
      </div>
      <p class="counter">{{ pos.cycle }} of {{ skill.cycles }}</p>
      <button type="button" class="quiet" @click="togglePause">
        {{ paused ? BUTTONS.resume : BUTTONS.pause }}
      </button>
    </template>

    <template v-else>
      <p v-if="closingText" class="instruction">{{ closingText }}</p>
      <button v-if="closingText" type="button" class="primary" @click="emit('finished', session.clientId)">
        {{ BUTTONS.continue }}
      </button>
    </template>
  </ExerciseFrame>
</template>

<style scoped>
.instruction {
  max-width: 28ch;
  font-size: 1.35rem;
  line-height: 1.5;
  margin: 0 0 24px;
}
.circle-area {
  width: 260px;
  height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.circle {
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: var(--circle);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  will-change: transform;
}
/* Reduced motion: no scaling. The label and a once-a-second countdown carry the pace. */
.circle.still {
  width: 180px;
  height: 180px;
  border: 3px solid var(--accent);
}
.circle.still.out {
  background: var(--circle-out);
}
.phase {
  font-size: 1.4rem;
  color: var(--text);
}
.seconds {
  font-size: 1.1rem;
  color: var(--muted);
  margin-top: 4px;
}
.counter {
  color: var(--faint);
  font-size: 0.95rem;
  margin: 16px 0 24px;
}
</style>
