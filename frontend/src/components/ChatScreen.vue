<script setup>
// "Talk it through": optional chat. The model may offer one skill; the user
// taps to start it (AGENTS.md rule 9). Model text appears only in assistant
// bubbles and never changes skill steps. The crisis phrase check runs on the
// backend before any model call; a match opens the crisis panel.
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { createConversation, getConversationMessages, listConversations, sendChatMessage } from '../api.js'
import { SKILLS } from '../content/skills.js'
import AppIcon from './AppIcon.vue'
import PageHeader from './PageHeader.vue'

const props = defineProps({ conversationId: { type: Number, default: null } })
const emit = defineEmits(['start', 'navigate', 'crisis'])

const STARTERS = ['Why are these exercises useful?', 'Explain the breathing rhythm', 'What is STOP for?']
const NEW = 'new'

const conversations = ref([])
const selected = ref(props.conversationId ?? NEW)
const messages = ref([])
const draft = ref('')
const sending = ref(false)
const notice = ref('')
const listEl = ref(null)
const loadingMessages = ref(false)

const lastReply = computed(() => [...messages.value].reverse().find((m) => m.role !== 'user'))
const offer = computed(() => (lastReply.value?.offer_skill ? SKILLS[lastReply.value.offer_skill] : null))
const showSkillLinks = computed(() => lastReply.value?.role === 'fallback')

const fmt = (iso) => new Date(iso).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
const preview = (c) => (c.first_line ? c.first_line.slice(0, 60) : `Conversation from ${fmt(c.created_at)}`)

async function loadList() {
  try {
    conversations.value = await listConversations()
  } catch {
    notice.value = "Past conversations can't be loaded right now. The skills and Crisis still work."
  }
}

async function loadMessages() {
  notice.value = ''
  if (selected.value === NEW) {
    messages.value = []
    return
  }
  loadingMessages.value = true
  try {
    messages.value = await getConversationMessages(selected.value)
    scrollDown()
  } catch {
    messages.value = []
    notice.value = "This conversation can't be loaded right now. The skills and Crisis still work."
  } finally {
    loadingMessages.value = false
  }
}

function scrollDown() {
  nextTick(() => listEl.value?.lastElementChild?.scrollIntoView({ block: 'end' }))
}

async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  sending.value = true
  notice.value = ''
  try {
    if (selected.value === NEW) {
      const c = await createConversation()
      selected.value = c.id
      await loadList()
    }
    const result = await sendChatMessage(selected.value, text)
    draft.value = ''
    messages.value.push(result.user, result.reply)
    if (result.crisis) emit('crisis')
    scrollDown()
    loadList()
  } catch {
    notice.value = "Messages can't be sent right now. The skills and Crisis still work."
  } finally {
    sending.value = false
  }
}

watch(selected, loadMessages)
onMounted(async () => {
  await loadList()
  await loadMessages()
})
</script>

<template>
  <main class="screen narrow chat">
    <!-- Always visible while the chat is open. -->
    <p class="limits">Coursework skills prototype. Not a therapist. Can't diagnose.</p>
    <PageHeader title="Talk it through" subtitle="Optional. Use fictional scenarios only. Nobody monitors this chat." />

    <label class="picker">
      <span class="sr">Conversation</span>
      <select v-model="selected">
        <option :value="NEW">New conversation</option>
        <option v-for="c in conversations" :key="c.id" :value="c.id">{{ preview(c) }}</option>
      </select>
    </label>

    <div v-if="messages.length === 0 && !loadingMessages" class="starters">
      <p class="section-label">{{ conversations.length ? 'Start a new conversation, or pick one above.' : 'No conversations yet. Where would you like to begin?' }}</p>
      <button v-for="s in STARTERS" :key="s" type="button" class="card starter" @click="draft = s">{{ s }}</button>
    </div>

    <p v-if="loadingMessages" class="muted" role="status">Loading this conversation</p>

    <ol v-if="messages.length" ref="listEl" class="messages">
      <li v-for="m in messages" :key="m.id" class="bubble" :class="m.role === 'user' ? 'mine' : 'theirs'">
        <p class="who">{{ m.role === 'user' ? 'You · fictional scenario' : 'Assistant' }} <span class="when">{{ fmt(m.created_at) }}</span></p>
        <p class="text">{{ m.text ?? '(This message was not saved.)' }}</p>
      </li>
    </ol>

    <div v-if="offer" class="offer">
      <button type="button" class="primary" @click="emit('start', offer.id)">Start {{ offer.label }}</button>
      <button type="button" class="link" @click="emit('navigate', 'activities')">Or choose another</button>
    </div>
    <div v-else-if="showSkillLinks" class="skill-links">
      <button v-for="id in ['breathing', 'stop', 'reframe']" :key="id" type="button" @click="emit('start', id)">
        {{ SKILLS[id].label }}
      </button>
    </div>

    <p v-if="notice" class="notice" role="status">{{ notice }}</p>

    <form class="composer card" @submit.prevent="send">
      <label class="sr" for="chat-input">Message</label>
      <textarea id="chat-input" v-model="draft" rows="3" maxlength="500" placeholder="Message" @keydown.enter.exact.prevent="send"></textarea>
      <button type="submit" class="send" :disabled="sending || !draft.trim()" aria-label="Send">
        <AppIcon name="arrow" :size="20" />
      </button>
    </form>
  </main>
</template>

<style scoped>
/* A slim bar, always visible while the chat is open. */
.limits {
  position: sticky;
  top: var(--space-2);
  z-index: 5;
  margin: 0 0 var(--space-4);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--secondary);
  color: var(--accent);
  font-size: var(--fs-sm);
  font-weight: 700;
}
/* Wide screens have a fixed top nav; keep the bar below it. */
@media (min-width: 900px) {
  .limits {
    top: calc(var(--tabbar-h) + var(--space-2));
  }
}
select,
textarea {
  outline-offset: 2px;
}
select:focus-visible,
textarea:focus-visible {
  outline: 3px solid var(--focus);
}
select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  font: inherit;
  color: var(--text);
}
.starters {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.starter {
  text-align: left;
  padding: 14px 16px;
  color: var(--accent);
  font-weight: 600;
}
.messages {
  list-style: none;
  padding: 0;
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
/* No card borders: the user's messages on the right in pale blue, the assistant's on the left in white. */
.bubble {
  max-width: 85%;
  padding: 10px 14px;
  border: 0;
}
.bubble.mine {
  align-self: flex-end;
  background: var(--secondary);
  border-radius: 18px 18px 4px 18px;
}
.bubble.theirs {
  align-self: flex-start;
  background: var(--surface);
  border-radius: 18px 18px 18px 4px;
}
.who {
  margin: 0 0 4px;
  font-size: 0.8rem;
  font-weight: 700;
}
.when {
  font-weight: 400;
  color: var(--muted);
}
.text {
  margin: 0;
  white-space: pre-wrap;
}
.offer,
.skill-links {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.skill-links {
  flex-direction: row;
  flex-wrap: wrap;
}
.skill-links button {
  flex: 1 1 160px;
}
.notice {
  color: var(--muted);
  font-size: 0.9rem;
}
.composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px;
}
.composer textarea {
  flex: 1;
  border: 0;
  resize: vertical;
  font: inherit;
  color: var(--text);
  background: none;
}
.send {
  flex: none;
  width: 44px;
  height: 44px;
  padding: 0;
  display: grid;
  place-items: center;
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  border-radius: 50%;
}
.send:disabled {
  opacity: 0.5;
}
</style>
