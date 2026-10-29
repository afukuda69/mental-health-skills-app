<script setup>
// The Crisis tab in the bottom bar, on every screen. Imports only content/crisis.js.
// Its label is always shown (other tabs are icon-only) so it never depends on
// recognising an icon.
import { CRISIS } from '../content/crisis.js'

defineEmits(['open'])
</script>

<template>
  <button type="button" class="crisis-button" @click="$emit('open')">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4.5-3 8-7 10c-4-2-7-5.5-7-10V6zm0 6v6m-3-3h6" />
    </svg>
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
  background: none;
  color: var(--crisis-text);
  font-size: 0.75rem;
  font-weight: 700;
}
.crisis-button svg {
  box-sizing: content-box;
  padding: 4px 15px;
  border-radius: 999px;
  background: var(--crisis-bg);
}
</style>
