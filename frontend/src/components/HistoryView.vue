<script setup>
// Date, skill, and how the session ended. The saved acknowledgment text is
// shown only on a deliberate tap; typed text is never shown (design.md g).
import { onMounted, reactive, ref } from 'vue'
import { getJSON } from '../api.js'
import { SKILLS } from '../content/skills.js'

defineEmits(['back'])

const state = ref('loading')
const sessions = ref([])
const open = reactive({})

const STATUS = { completed: 'Finished', stopped: 'Stopped early', left: 'Left the page' }

const formatDate = (iso) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

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
    <ul v-else>
      <li v-for="s in sessions" :key="s.id">
        <div class="row">
          <span>{{ formatDate(s.started_at) }} · {{ SKILLS[s.skill]?.label ?? s.skill }} · {{ STATUS[s.end_reason] ?? 'Not finished' }}</span>
          <button v-if="s.messages.length" type="button" class="link" @click="open[s.id] = !open[s.id]">
            {{ open[s.id] ? 'Hide message' : 'Show message' }}
          </button>
        </div>
        <p v-for="(m, i) in open[s.id] ? s.messages : []" :key="i" class="message">{{ m.text }}</p>
      </li>
    </ul>
    <button type="button" class="link" @click="$emit('back')">Back to start</button>
  </main>
</template>

<style scoped>
.history ul {
  list-style: none;
  padding: 0;
  width: 100%;
  max-width: 520px;
  text-align: left;
}
.history li {
  padding: 12px 0;
  border-top: 1px solid var(--line);
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.message {
  margin: 8px 0 0;
  color: var(--muted);
}
.muted {
  color: var(--muted);
}
</style>
