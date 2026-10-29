<script setup>
// The one local profile, stored in SQLite on this computer. Each item shows
// where it came from (you chose it, or the app learned it from history) and
// how to change it. Counts update as soon as a session ends.
import { ref, watch } from 'vue'
import { deleteAllHistory, resetProfile, updateProfile } from '../api.js'
import { CHECKIN_LABELS, SKILLS } from '../content/skills.js'
import HistoryView from './HistoryView.vue'

const props = defineProps({ profile: { type: Object, default: null } })
const emit = defineEmits(['changed', 'open-conversation'])

const nameDraft = ref(props.profile?.display_name ?? '')
const notice = ref('')
const confirming = ref(false)
const historyKey = ref(0)
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
  <main class="screen profile">
    <h1>Profile</h1>
    <p class="muted intro">One local profile, saved on this computer only. Nobody else sees it.</p>

    <p v-if="!profile" class="muted">The profile can't be loaded right now.</p>
    <template v-else>
      <div class="card item">
        <label for="display-name" class="item-title">Display name</label>
        <p class="source">{{ profile.display_name ? 'You chose this' : 'Not set (optional)' }}</p>
        <form class="inline" @submit.prevent="save({ display_name: nameDraft || null }, 'Name saved.')">
          <input id="display-name" v-model="nameDraft" type="text" maxlength="40" autocomplete="off" />
          <button type="submit">Save</button>
        </form>
      </div>

      <div class="card item">
        <label for="usual-skill" class="item-title">Usual skill</label>
        <p class="value">{{ profile.usual_skill ? SKILLS[profile.usual_skill].label : 'None yet' }}</p>
        <p class="source">
          {{ SOURCE[profile.usual_source] ?? 'Learned after your first finished session' }}
          <template v-if="profile.usual_source === 'chosen' && profile.learned_usual">
            (learned would be {{ SKILLS[profile.learned_usual].label }})
          </template>
        </p>
        <select
          id="usual-skill"
          :value="profile.usual_source === 'chosen' ? profile.usual_skill : ''"
          @change="save({ usual_skill: $event.target.value || null }, 'Usual skill saved.')"
        >
          <option value="">Let the app learn it</option>
          <option v-for="s in Object.values(SKILLS)" :key="s.id" :value="s.id">{{ s.label }}</option>
        </select>
      </div>

      <div class="card item">
        <label for="animate-circle" class="item-title">Animate the breathing circle</label>
        <p class="value">{{ profile.animate_circle === null ? 'System setting' : profile.animate_circle ? 'On' : 'Off' }}</p>
        <p class="source">{{ SOURCE[profile.animate_source] }}</p>
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

      <div class="card item">
        <p class="item-title">Last check-in</p>
        <p class="value">{{ profile.last_checkin ? CHECKIN_LABELS[profile.last_checkin] : 'None' }}</p>
        <p class="source">{{ profile.last_checkin ? `You chose this on Home, ${fmt(profile.last_checkin_at)}` : 'Chosen on Home' }}</p>
      </div>

      <div class="card item">
        <p class="item-title">Sessions per skill</p>
        <p class="source">Counted from your history</p>
        <ul class="counts">
          <li v-for="(c, id) in profile.counts" :key="id">
            <strong>{{ SKILLS[id].label }}</strong>: {{ c.completed }} completed, {{ c.stopped }} stopped, {{ c.left }} left
          </li>
        </ul>
      </div>

      <div class="actions">
        <button type="button" @click="reset">Reset to learned</button>
        <button v-if="!confirming" type="button" class="danger-soft" @click="confirming = true">Delete all</button>
        <div v-else class="card confirm" role="group" aria-label="Confirm delete">
          <p>Delete the profile, every saved practice, and every conversation? This can't be undone.</p>
          <button type="button" class="danger-soft" @click="deleteAll">Delete all</button>
          <button type="button" @click="confirming = false">Keep everything</button>
        </div>
      </div>
      <p v-if="notice" class="muted" role="status">{{ notice }}</p>
    </template>

    <HistoryView :key="historyKey + (profile?.updated_at ?? '')" @open-conversation="emit('open-conversation', $event)" />
  </main>
</template>

<style scoped>
.intro {
  margin: -8px 0 16px;
}
.item {
  margin-bottom: 12px;
}
.item-title {
  display: block;
  margin: 0;
  font-weight: 700;
}
.value {
  margin: 2px 0 0;
}
.source {
  margin: 2px 0 10px;
  font-size: 0.85rem;
  color: var(--muted);
}
.inline {
  display: flex;
  gap: 8px;
}
.inline input {
  flex: 1;
}
select {
  width: 100%;
}
.counts {
  margin: 0;
  padding-left: 18px;
}
.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}
.confirm {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.confirm p {
  margin: 0;
}
</style>
