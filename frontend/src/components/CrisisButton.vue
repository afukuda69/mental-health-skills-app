<script setup>
// Rendered by App.vue's root layout on every screen. Imports only content/crisis.js.
import { CRISIS } from '../content/crisis.js'

defineEmits(['open'])
</script>

<template>
  <button type="button" class="crisis-button" @click="$emit('open')">{{ CRISIS.title }}</button>
</template>

<style scoped>
.crisis-button {
  position: fixed;
  top: 12px;
  right: 16px;
  z-index: 100;
  padding: 8px 14px;
  border: 1.5px solid var(--crisis-border);
  border-radius: 999px;
  background: var(--crisis-bg);
  color: var(--crisis-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.crisis-button:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 2px;
}
</style>
