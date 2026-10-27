<script setup>
import { ref } from 'vue'
import { BUTTONS, DONE } from '../content/skills.js'

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
  <main class="screen">
    <h1>{{ stopped ? DONE.stopped : DONE.finished }}</h1>
    <div class="options">
      <button type="button" class="primary" @click="$emit('restart')">{{ BUTTONS.backToStart }}</button>
      <button type="button" @click="close">{{ BUTTONS.close }}</button>
    </div>
    <p v-if="showCloseHint" class="hint">{{ DONE.closeHint }}</p>
  </main>
</template>

<style scoped>
.options {
  display: flex;
  gap: 12px;
}
.hint {
  margin-top: 16px;
  color: var(--muted);
}
</style>
