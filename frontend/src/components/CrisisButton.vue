<script setup>
// The Crisis tab in the bottom bar, on every screen. Imports only content/crisis.js.
// Text label only, like the other tabs.
import { CRISIS } from '../content/crisis.js'

defineEmits(['open'])
</script>

<template>
  <button type="button" class="crisis-button" @click="$emit('open')">
    <span>{{ CRISIS.tab }}</span>
  </button>
</template>

<style scoped>
/* Warm muted coral, distinct from the blue UI. */
.crisis-button {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  padding: 4px;
  border: 0;
  border-radius: 999px;
  background: var(--crisis-bg);
  color: var(--crisis-text);
  font-size: 0.9rem;
  font-weight: 700;
}

</style>
