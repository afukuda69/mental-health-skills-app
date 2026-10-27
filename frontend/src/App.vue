<script setup>
// Root layout. The tab bar (with the Crisis tab) and CrisisPanel sit outside
// every v-if, so the Crisis tab shows on every screen, including the
// exercise, loading and error states. While the exercise runs, the bar
// contracts to the Crisis tab alone (D1: no navigation inside an exercise).
import { computed, onMounted, ref } from 'vue'
import { getJSON, send } from './api.js'
import BreathingSkill from './components/BreathingSkill.vue'
import CheckIn from './components/CheckIn.vue'
import CrisisPanel from './components/CrisisPanel.vue'
import DoneScreen from './components/DoneScreen.vue'
import HistoryView from './components/HistoryView.vue'
import HomeScreen from './components/HomeScreen.vue'
import TabBar from './components/TabBar.vue'

const SKILL_COMPONENTS = { breathing: BreathingSkill }

const screen = ref('home')
const crisisOpen = ref(false)
const usualSkill = ref(null)
const entryChoice = ref(null)
const skillId = ref(null)
const setupMs = ref(0)
const stopped = ref(false)
let lastClientId = null
let entryShownAt = performance.now()

const activeTab = computed(() => (screen.value === 'history' ? 'history' : screen.value === 'home' ? 'home' : null))

async function loadUsual() {
  try {
    usualSkill.value = (await getJSON('/usual', 3000)).skill
  } catch {
    usualSkill.value = null // no usual label; the practice still starts
  }
}

function toHome() {
  screen.value = 'home'
  entryChoice.value = null
  stopped.value = false
  entryShownAt = performance.now()
  loadUsual()
}

function navigate(to) {
  if (to === 'home') toHome()
  else screen.value = to
}

function startSkill(id) {
  skillId.value = id
  // Entry is timed separately from the exercise (design.md section d).
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
  <HomeScreen
    v-if="screen === 'home'"
    :usual-skill="usualSkill"
    :entry-choice="entryChoice"
    @choose="entryChoice = $event"
    @start="startSkill"
    @history="screen = 'history'"
  />
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
  <DoneScreen v-else-if="screen === 'done'" :stopped="stopped" @restart="toHome" />
  <HistoryView v-else-if="screen === 'history'" @navigate="navigate" />

  <TabBar :active="activeTab" :contracted="screen === 'exercise'" @navigate="navigate" @crisis="crisisOpen = true" />
  <CrisisPanel v-if="crisisOpen" @close="crisisOpen = false" />
</template>
