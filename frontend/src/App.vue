<script setup>
// Root layout. CrisisButton and CrisisPanel sit outside every v-if, so they
// show on every screen, including loading and error states.
import { onMounted, ref } from 'vue'
import { getJSON, send } from './api.js'
import BreathingSkill from './components/BreathingSkill.vue'
import CheckIn from './components/CheckIn.vue'
import CrisisButton from './components/CrisisButton.vue'
import CrisisPanel from './components/CrisisPanel.vue'
import DoneScreen from './components/DoneScreen.vue'
import EntryScreen from './components/EntryScreen.vue'
import HistoryView from './components/HistoryView.vue'
import SkillPicker from './components/SkillPicker.vue'

const SKILL_COMPONENTS = { breathing: BreathingSkill }

const screen = ref('entry')
const crisisOpen = ref(false)
const usualSkill = ref(null)
const entryChoice = ref(null)
const skillId = ref(null)
const setupMs = ref(0)
const stopped = ref(false)
let lastClientId = null
let entryShownAt = performance.now()

async function loadUsual() {
  try {
    usualSkill.value = (await getJSON('/usual', 3000)).skill
  } catch {
    usualSkill.value = null // no button; the picker still works
  }
}

function toEntry() {
  screen.value = 'entry'
  entryChoice.value = null
  stopped.value = false
  entryShownAt = performance.now()
  loadUsual()
}

function choose(key) {
  entryChoice.value = key
  screen.value = 'picker'
}

function startSkill(id) {
  skillId.value = id
  setupMs.value = performance.now() - entryShownAt
  screen.value = 'exercise'
}

function onFinished(clientId) {
  lastClientId = clientId
  screen.value = 'checkin'
}

function onStopped() {
  stopped.value = true
  screen.value = 'done'
}

function onAnswer(rating) {
  if (rating && lastClientId) send(`/sessions/${lastClientId}/feedback`, { rating })
  screen.value = 'done'
}

onMounted(loadUsual)
</script>

<template>
  <CrisisButton @open="crisisOpen = true" />

  <EntryScreen
    v-if="screen === 'entry'"
    :usual-skill="usualSkill"
    @choose="choose"
    @use-usual="startSkill(usualSkill)"
    @history="screen = 'history'"
  />
  <SkillPicker v-else-if="screen === 'picker'" :usual-skill="usualSkill" @pick="startSkill" @back="toEntry" />
  <component
    :is="SKILL_COMPONENTS[skillId]"
    v-else-if="screen === 'exercise'"
    :entry-choice="entryChoice"
    :setup-ms="setupMs"
    :crisis-open="crisisOpen"
    @finished="onFinished"
    @stopped="onStopped"
  />
  <CheckIn v-else-if="screen === 'checkin'" @answer="onAnswer" />
  <DoneScreen v-else-if="screen === 'done'" :stopped="stopped" @restart="toEntry" />
  <HistoryView v-else-if="screen === 'history'" @back="toEntry" />

  <CrisisPanel v-if="crisisOpen" @close="crisisOpen = false" />
</template>
