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
    <div class="card done">
      <h1>{{ stopped ? DONE.stopped : DONE.finished }}</h1>
      <div class="actions">
        <button type="button" class="primary" @click="$emit('restart')">{{ BUTTONS.backToStart }}</button>
        <button type="button" @click="close">{{ BUTTONS.close }}</button>
      </div>
      <p v-if="showCloseHint" class="muted hint">{{ DONE.closeHint }}</p>
    </div>
  </main>
</template>

<style scoped>
.done h1 {
  font-size: 1.6rem;
}
.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hint {
  margin: 14px 0 0;
}
</style>
