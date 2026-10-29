<script setup>
// Root layout. The tab bar (with the Crisis tab) and CrisisPanel sit outside
// every v-if, so Crisis shows on every screen, including exercises, loading and
// error states. During an exercise, and on the contracted "Overwhelmed" Home,
// the bar contracts to the Crisis tab alone (D1).
import { computed, onMounted, ref } from 'vue'
import { getProfile, send, updateProfile } from './api.js'
import { SKILLS } from './content/skills.js'
import ActivitiesScreen from './components/ActivitiesScreen.vue'
import BreathingSkill from './components/BreathingSkill.vue'
import ChatScreen from './components/ChatScreen.vue'
import CheckIn from './components/CheckIn.vue'
import CrisisPanel from './components/CrisisPanel.vue'
import DoneScreen from './components/DoneScreen.vue'
import HomeScreen from './components/HomeScreen.vue'
import ProfileScreen from './components/ProfileScreen.vue'
import ReframeSkill from './components/ReframeSkill.vue'
import StopSkill from './components/StopSkill.vue'
import TabBar from './components/TabBar.vue'

const SKILL_COMPONENTS = { breathing: BreathingSkill, stop: StopSkill, reframe: ReframeSkill }

const screen = ref('home')
const crisisOpen = ref(false)
const profile = ref(null)
const checkin = ref(null)
const showEverything = ref(false)
const skillId = ref(null)
const setupMs = ref(0)
const runKey = ref(0)
const stopped = ref(false)
const chatConversationId = ref(null)
let lastClientId = null
let navShownAt = performance.now()

const contractedHome = computed(() => screen.value === 'home' && checkin.value === 'overwhelmed' && !showEverything.value)
const activeTab = computed(() => {
  if (['exercise', 'checkin', 'done'].includes(screen.value)) return 'activities'
  return screen.value
})
// Sent with the session as the entry choice (Skip sends none), as in 3.2.
const entryChoice = computed(() => (checkin.value && checkin.value !== 'skip' ? checkin.value : null))

async function loadProfile() {
  try {
    profile.value = await getProfile()
  } catch {
    profile.value = null // Home falls back to breathing; every skill still starts
  }
}

function navigate(to, conversationId = null) {
  chatConversationId.value = to === 'chat' ? conversationId : null
  screen.value = to
  if (to === 'home' || to === 'activities' || to === 'profile') {
    navShownAt = performance.now()
    loadProfile()
  }
}

function chooseCheckin(key) {
  checkin.value = key
  showEverything.value = false
  if (key) updateProfile({ last_checkin: key }).then((p) => (profile.value = p)).catch(() => {})
}

function startSkill(id) {
  if (!SKILLS[id]?.available) return
  skillId.value = id
  stopped.value = false
  // Entry and skill pick are timed separately from the exercise (design.md section d).
  setupMs.value = performance.now() - navShownAt
  runKey.value += 1
  screen.value = 'exercise'
}

function onFinished(clientId) {
  lastClientId = clientId
  screen.value = 'checkin'
}

function onStopped() {
  stopped.value = true
  screen.value = 'done'
  loadProfile()
}

function onAnswer(rating) {
  if (rating && lastClientId) send(`/sessions/${lastClientId}/feedback`, { rating })
  screen.value = 'done'
  setTimeout(loadProfile, 300) // after the fire-and-forget writes land
}

function onAnimateChange(value) {
  updateProfile({ animate_circle: value }).then((p) => (profile.value = p)).catch(() => {})
}

function backToHome() {
  checkin.value = null
  showEverything.value = false
  navigate('home')
}

onMounted(loadProfile)
</script>

<template>
  <HomeScreen
    v-if="screen === 'home'"
    :profile="profile"
    :checkin="checkin"
    :show-everything="showEverything"
    @checkin="chooseCheckin"
    @show-everything="showEverything = true"
    @start="startSkill"
    @navigate="navigate"
    @crisis="crisisOpen = true"
  />
  <ActivitiesScreen v-else-if="screen === 'activities'" :usual-skill="profile?.usual_skill ?? null" @start="startSkill" @navigate="navigate" />
  <component
    :is="SKILL_COMPONENTS[skillId]"
    v-else-if="screen === 'exercise'"
    :key="runKey"
    :entry-choice="entryChoice"
    :setup-ms="setupMs"
    :crisis-open="crisisOpen"
    :animate-pref="profile?.animate_circle ?? null"
    @finished="onFinished"
    @stopped="onStopped"
    @crisis="crisisOpen = true"
    @animate-change="onAnimateChange"
  />
  <CheckIn v-else-if="screen === 'checkin'" @answer="onAnswer" />
  <DoneScreen v-else-if="screen === 'done'" :stopped="stopped" @restart="backToHome" />
  <ChatScreen
    v-else-if="screen === 'chat'"
    :key="chatConversationId ?? 'new'"
    :conversation-id="chatConversationId"
    @start="startSkill"
    @navigate="navigate"
    @crisis="crisisOpen = true"
  />
  <ProfileScreen
    v-else-if="screen === 'profile'"
    :profile="profile"
    @changed="(p) => (p ? (profile = p) : loadProfile())"
    @open-conversation="navigate('chat', $event)"
  />

  <TabBar
    :active="activeTab"
    :contracted="screen === 'exercise' || contractedHome"
    @navigate="navigate"
    @crisis="crisisOpen = true"
  />
  <CrisisPanel v-if="crisisOpen" @close="crisisOpen = false" />
</template>
