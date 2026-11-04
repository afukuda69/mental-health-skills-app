<script setup>
import { ref } from 'vue'
import { BUTTONS, DONE } from '../content/skills.js'
import PageHeader from './PageHeader.vue'

defineProps({ stopped: { type: Boolean, default: false } })
defineEmits(['restart'])

const showCloseHint = ref(false)

// Browsers only let scripts close tabs they opened, so show a hint if the tab stays open.
function close() {
  window.close()
  setTimeout(() => (showCloseHint.value = true), 300)
}
</script>

<template>
  <main class="screen narrow">
    <PageHeader :title="stopped ? DONE.stopped : DONE.finished" :subtitle="DONE.note" />
    <div class="actions">
      <button type="button" class="primary" @click="$emit('restart')">{{ BUTTONS.backToStart }}</button>
      <button type="button" @click="close">{{ BUTTONS.close }}</button>
    </div>
    <p v-if="showCloseHint" class="muted hint" role="status">{{ DONE.closeHint }}</p>
  </main>
</template>

<style scoped>
.actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.hint {
  margin: var(--space-3) 0 0;
}
</style>
