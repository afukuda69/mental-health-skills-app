<script setup>
// One card per session, newest first: skill, date, status, active and planned
// time, and how it ended, in neutral wording. No totals, streaks, or scores
// (D6). The saved acknowledgment text is shown only on a deliberate tap;
// typed text is never shown (design.md section g).
import { onMounted, reactive, ref } from 'vue'
import { getJSON } from '../api.js'
import { SKILLS } from '../content/skills.js'
import { plannedMs } from '../timing.js'

defineEmits(['navigate'])

const state = ref('loading')
const sessions = ref([])
const open = reactive({})

const STATUS = { completed: 'Completed', stopped: 'Stopped', left: 'Left' }
const ENDED = {
  completed: 'Finished all seven cycles',
  stopped: 'Stopped with Stop exercise',
  left: 'Left the page',
}

const fmt = (iso) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const seconds = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(1)} s`)
// The planned time comes from the schedule in content/skills.js, as in the session record.
const planned = (s) => (SKILLS[s.skill]?.cycles ? plannedMs(SKILLS[s.skill]) : null)

onMounted(async () => {
  try {
    sessions.value = (await getJSON('/history')).sessions
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
})
</script>

<template>
  <main class="screen history">
    <h1>History</h1>
    <p v-if="state === 'loading'" class="muted">Loading</p>
    <p v-else-if="state === 'error'" class="muted">History can't be loaded right now.</p>
    <p v-else-if="sessions.length === 0" class="muted">No sessions yet.</p>
    <ul v-else class="list">
      <li v-for="s in sessions" :key="s.id" class="row">
        <div class="line">
          <span class="dot" :class="s.end_reason ?? 'none'" aria-hidden="true"></span>
          <strong class="status">{{ STATUS[s.end_reason] ?? 'Not finished' }}</strong>
          <span class="skill">{{ SKILLS[s.skill]?.label ?? s.skill }}</span>
          <span class="muted when">{{ fmt(s.started_at) }}</span>
        </div>
        <p class="muted detail">
          Active {{ seconds(s.measured_ms) }} of {{ seconds(planned(s)) }} planned · {{ ENDED[s.end_reason] ?? 'No end was recorded' }}
        </p>
        <button v-if="s.messages.length" type="button" class="link" @click="open[s.id] = !open[s.id]">
          {{ open[s.id] ? 'Hide message' : 'Show message' }}
        </button>
        <p v-for="(m, i) in open[s.id] ? s.messages : []" :key="i" class="muted message">{{ m.text }}</p>
      </li>
    </ul>
    <button type="button" class="link back" @click="$emit('navigate', 'home')">Back to start</button>
  </main>
</template>

<style scoped>
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.row {
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}
.row:last-child {
  border-bottom: 0;
}
.line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--status-left);
}
.dot.completed {
  background: var(--status-completed);
}
.dot.stopped {
  background: var(--status-stopped);
}
.dot.none {
  background: none;
  border: 2px solid var(--status-left);
}
.when {
  margin-left: auto;
  font-size: 0.85rem;
}
.detail {
  margin: 4px 0 0 18px;
  font-size: 0.9rem;
}
.message {
  margin: 6px 0 0 18px;
}
.row .link {
  margin-left: 14px;
}
.back {
  margin-top: 16px;
}
</style>
