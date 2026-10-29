<script setup>
// History, shown inside Profile: one compact row per session (status dot,
// active vs planned time) and one per conversation (tap to open). No totals,
// streaks, or scores (D6). Saved acknowledgment text only on a deliberate tap;
// typed reframe text is never stored.
import { onMounted, reactive, ref } from 'vue'
import { getJSON } from '../api.js'
import { SKILLS } from '../content/skills.js'
import { plannedMs } from '../timing.js'

const props = defineProps({ refreshKey: { type: Number, default: 0 } })
const emit = defineEmits(['open-conversation'])

const state = ref('loading')
const sessions = ref([])
const conversations = ref([])
const open = reactive({})

const STATUS = { completed: 'Completed', stopped: 'Stopped', left: 'Left' }
const ENDED = { completed: 'Finished every step', stopped: 'Stopped with Stop exercise', left: 'Left the exercise' }

const fmt = (iso) => new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
const seconds = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(1)} s`)
const planned = (s) => s.planned_ms ?? (SKILLS[s.skill] ? plannedMs(SKILLS[s.skill]) : null)

async function load() {
  try {
    const data = await getJSON('/history')
    sessions.value = data.sessions
    conversations.value = data.conversations ?? []
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}
onMounted(load)
defineExpose({ load, refreshKey: props.refreshKey })
</script>

<template>
  <section class="history" aria-labelledby="history-title">
    <h2 id="history-title">History</h2>
    <p v-if="state === 'loading'" class="muted">Loading</p>
    <p v-else-if="state === 'error'" class="muted">History can't be loaded right now.</p>
    <p v-else-if="sessions.length === 0 && conversations.length === 0" class="muted">Nothing saved yet.</p>
    <template v-else>
      <ul v-if="sessions.length" class="list">
        <li v-for="s in sessions" :key="s.id" class="row">
          <div class="line">
            <span class="dot" :class="s.end_reason ?? 'none'" aria-hidden="true"></span>
            <strong>{{ STATUS[s.end_reason] ?? 'Not finished' }}</strong>
            <span>{{ SKILLS[s.skill]?.label ?? s.skill }}</span>
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
      <template v-if="conversations.length">
        <p class="section-label">Conversations</p>
        <div class="list">
          <button v-for="c in conversations" :key="c.id" type="button" class="list-row" @click="emit('open-conversation', c.id)">
            <span><span class="title">{{ c.first_line ?? 'Conversation' }}</span><span class="sub">{{ fmt(c.created_at) }} · {{ c.message_count }} messages</span></span>
          </button>
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.history {
  margin-top: 28px;
}
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
</style>
