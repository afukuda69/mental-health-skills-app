<script setup>
// The one local profile, stored in SQLite on this computer. Each item shows
// where it came from (you chose it, or the app learned it from history) and
// how to change it. Counts update as soon as a session ends.
import { ref, watch } from 'vue'
import { deleteAllHistory, resetProfile, updateProfile } from '../api.js'
import { CHECKIN_LABELS, SKILLS } from '../content/skills.js'
import AppIcon from './AppIcon.vue'
import HistoryView from './HistoryView.vue'
import PageHeader from './PageHeader.vue'

const props = defineProps({ profile: { type: Object, default: null } })
const emit = defineEmits(['changed', 'open-conversation', 'navigate', 'retry'])

const nameDraft = ref(props.profile?.display_name ?? '')
const notice = ref('')
const confirming = ref(false)
const historyKey = ref(0)
// Which settings row is open for editing (one at a time).
const editing = ref(null)
const toggle = (row) => (editing.value = editing.value === row ? null : row)
const usualLabel = (pr) => (pr.usual_skill ? SKILLS[pr.usual_skill].label : 'None yet')
const animateLabel = (pr) => (pr.animate_circle === null ? 'System setting' : pr.animate_circle ? 'On' : 'Off')
watch(
  () => props.profile?.display_name,
  (n) => (nameDraft.value = n ?? ''),
)

const SOURCE = { chosen: 'You chose this', learned: 'Learned from your history', system: 'Follows your system motion setting' }
const fmt = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' }) : '')

async function save(changes, message) {
  try {
    emit('changed', await updateProfile(changes))
    notice.value = message
  } catch {
    notice.value = "That couldn't be saved right now."
  }
}

async function reset() {
  try {
    emit('changed', await resetProfile())
    notice.value = 'Reset to what the app learned from your history.'
  } catch {
    notice.value = "That couldn't be reset right now."
  }
}

async function deleteAll() {
  try {
    await deleteAllHistory()
    emit('changed', null)
    historyKey.value += 1
    notice.value = 'Profile and history deleted.'
  } catch {
    notice.value = "That couldn't be deleted right now."
  }
  confirming.value = false
}
</script>

<template>
  <main class="screen narrow profile">
    <PageHeader title="Profile" subtitle="What the app remembers, saved only on this computer." />

    <div v-if="!profile" class="state-note" role="status">
      <p class="state-title">The profile can't be loaded right now</p>
      <p class="state-text">The skills and Crisis still work.</p>
      <button type="button" @click="emit('retry')">Try again</button>
    </div>
    <template v-else>
      <p class="group-label">About you</p>
      <div class="group">
        <button type="button" class="setting" :aria-expanded="editing === 'name'" @click="toggle('name')">
          <span class="left"><span class="label">Display name</span><span class="source">{{ profile.display_name ? 'You chose this' : 'Optional' }}</span></span>
          <span class="value">{{ profile.display_name ?? 'Not set' }}</span>
          <AppIcon class="chevron" :class="{ open: editing === 'name' }" name="chevron" :size="18" />
        </button>
        <form v-if="editing === 'name'" class="editor" @submit.prevent="save({ display_name: nameDraft || null }, 'Name saved.')">
          <label for="display-name" class="sr">Display name</label>
          <input id="display-name" v-model="nameDraft" type="text" maxlength="40" autocomplete="off" />
          <button type="submit">Save</button>
        </form>
      </div>

      <p class="group-label">Preferences</p>
      <div class="group">
        <button type="button" class="setting" :aria-expanded="editing === 'usual'" @click="toggle('usual')">
          <span class="left">
            <span class="label">Usual skill</span>
            <span class="source">
              {{ SOURCE[profile.usual_source] ?? 'Learned after your first finished session' }}<template v-if="profile.usual_source === 'chosen' && profile.learned_usual"> (learned: {{ SKILLS[profile.learned_usual].label }})</template>
            </span>
          </span>
          <span class="value">{{ usualLabel(profile) }}</span>
          <AppIcon class="chevron" :class="{ open: editing === 'usual' }" name="chevron" :size="18" />
        </button>
        <div v-if="editing === 'usual'" class="editor">
          <label for="usual-skill" class="sr">Usual skill</label>
          <select
            id="usual-skill"
            :value="profile.usual_source === 'chosen' ? profile.usual_skill : ''"
            @change="save({ usual_skill: $event.target.value || null }, 'Usual skill saved.')"
          >
            <option value="">Let the app learn it</option>
            <option v-for="s in Object.values(SKILLS)" :key="s.id" :value="s.id">{{ s.label }}</option>
          </select>
        </div>

        <button type="button" class="setting" :aria-expanded="editing === 'animate'" @click="toggle('animate')">
          <span class="left"><span class="label">Animate the breathing circle</span><span class="source">{{ SOURCE[profile.animate_source] }}</span></span>
          <span class="value">{{ animateLabel(profile) }}</span>
          <AppIcon class="chevron" :class="{ open: editing === 'animate' }" name="chevron" :size="18" />
        </button>
        <div v-if="editing === 'animate'" class="editor">
          <label for="animate-circle" class="sr">Animate the breathing circle</label>
          <select
            id="animate-circle"
            :value="profile.animate_circle === null ? '' : String(profile.animate_circle)"
            @change="save({ animate_circle: $event.target.value === '' ? null : $event.target.value === 'true' }, 'Motion setting saved.')"
          >
            <option value="">Follow the system setting</option>
            <option value="true">On</option>
            <option value="false">Off</option>
          </select>
        </div>
      </div>

      <p class="group-label">Activity</p>
      <div class="group">
        <div class="setting static">
          <span class="left"><span class="label">Last check-in</span><span class="source">{{ profile.last_checkin ? `Chosen on Home, ${fmt(profile.last_checkin_at)}` : 'Chosen on Home' }}</span></span>
          <span class="value">{{ profile.last_checkin ? CHECKIN_LABELS[profile.last_checkin] : 'None' }}</span>
        </div>
        <button type="button" class="setting" :aria-expanded="editing === 'counts'" @click="toggle('counts')">
          <span class="left"><span class="label">Sessions per skill</span><span class="source">Counted from your history</span></span>
          <span class="value">{{ Object.values(profile.counts).reduce((n, c) => n + c.completed + c.stopped + c.left, 0) }}</span>
          <AppIcon class="chevron" :class="{ open: editing === 'counts' }" name="chevron" :size="18" />
        </button>
        <ul v-if="editing === 'counts'" class="editor counts">
          <li v-for="(c, id) in profile.counts" :key="id">
            <strong>{{ SKILLS[id].label }}</strong>: {{ c.completed }} completed, {{ c.stopped }} stopped, {{ c.left }} left
          </li>
        </ul>
      </div>

      <p class="group-label">Your data</p>
      <div class="group">
        <button type="button" class="setting action" @click="reset">
          <span class="label">Reset to learned</span>
          <span class="value small">Clears your choices</span>
        </button>
        <button v-if="!confirming" type="button" class="setting action danger" @click="confirming = true">
          <span class="label">Delete all</span>
        </button>
        <div v-else class="editor confirm" role="group" aria-label="Confirm delete">
          <p>Delete the profile, every saved practice, and every conversation? This can't be undone.</p>
          <button type="button" class="danger-soft" @click="deleteAll">Delete all</button>
          <button type="button" @click="confirming = false">Keep everything</button>
        </div>
      </div>
      <p v-if="notice" class="muted" role="status">{{ notice }}</p>
    </template>

    <HistoryView
      :key="historyKey + (profile?.updated_at ?? '')"
      @open-conversation="emit('open-conversation', $event)"
      @navigate="emit('navigate', $event)"
    />
  </main>
</template>

<style scoped>
.group-label {
  margin: var(--space-5) var(--space-1) var(--space-2);
  font-weight: 700;
  color: var(--muted);
}
/* Settings-style group: rows separated by hairlines, no cards. */
.group {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.setting {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 56px;
  padding: 12px 16px;
  border: 0;
  border-top: 1px solid var(--line);
  border-radius: 0;
  background: none;
  color: var(--text);
  font-weight: 400;
  text-align: left;
}
.group > .setting:first-child {
  border-top: 0;
}
.left {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.label {
  font-weight: 600;
}
.source {
  font-size: 0.8rem;
  color: var(--muted);
}
.value {
  margin-left: auto;
  text-align: right;
  color: var(--muted);
}
.value.small {
  font-size: 0.85rem;
}
.chevron {
  flex: none;
  color: var(--muted);
}
.chevron.open {
  transform: rotate(90deg);
}
.action .label {
  color: var(--accent);
}
.danger .label {
  color: var(--crisis-text);
}
.editor {
  display: flex;
  gap: 8px;
  padding: 0 16px 14px;
}
.editor input,
.editor select {
  flex: 1;
}
.counts {
  flex-direction: column;
  margin: 0;
  padding-left: 34px;
}
.confirm {
  flex-direction: column;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.confirm p {
  margin: 0;
}
</style>
