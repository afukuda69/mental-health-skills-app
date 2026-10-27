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
const seconds = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(1)} seconds`)
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
    <template v-else>
      <article v-for="s in sessions" :key="s.id" class="card entry">
        <div class="head">
          <div>
            <h2>{{ SKILLS[s.skill]?.label ?? s.skill }}</h2>
            <p class="muted when">{{ fmt(s.started_at) }}</p>
          </div>
          <span class="chip status" :class="s.end_reason">{{ STATUS[s.end_reason] ?? 'Not finished' }}</span>
        </div>
        <dl class="facts">
          <div><dt>Active time</dt><dd>{{ seconds(s.measured_ms) }}</dd></div>
          <div><dt>Planned time</dt><dd>{{ seconds(planned(s)) }}</dd></div>
          <div class="wide"><dt>How it ended</dt><dd>{{ ENDED[s.end_reason] ?? 'No end was recorded' }}</dd></div>
        </dl>
        <button v-if="s.messages.length" type="button" class="link" @click="open[s.id] = !open[s.id]">
          {{ open[s.id] ? 'Hide message' : 'Show message' }}
        </button>
        <p v-for="(m, i) in open[s.id] ? s.messages : []" :key="i" class="muted message">{{ m.text }}</p>
      </article>
    </template>
    <button type="button" class="link" @click="$emit('navigate', 'home')">Back to start</button>
  </main>
</template>

<style scoped>
.entry {
  margin-bottom: 12px;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.head h2 {
  font-size: 1.15rem;
  margin: 0;
}
.when {
  margin: 2px 0 0;
  font-size: 0.9rem;
}
.status.completed {
  background: var(--sage);
  border-color: var(--sage-strong);
  color: var(--accent);
}
.facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 14px 0 6px;
}
.facts .wide {
  grid-column: 1 / -1;
}
dt {
  font-size: 0.85rem;
  color: var(--muted);
}
dd {
  margin: 0;
  font-weight: 600;
}
.message {
  margin: 6px 0 0;
}
</style>
