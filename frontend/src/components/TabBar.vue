<script setup>
// Bottom navigation: only the screens 3.2 has. The Crisis tab is CrisisButton,
// which imports only static content, so it works with the backend down.
// While an exercise runs, the bar contracts to the Crisis tab alone (D1).
import AppIcon from './AppIcon.vue'
import CrisisButton from './CrisisButton.vue'

defineProps({
  active: { type: String, default: null },
  contracted: { type: Boolean, default: false },
})
defineEmits(['navigate', 'crisis'])

const TABS = [
  { id: 'home', label: 'Home', icon: 'home' },
  { id: 'history', label: 'History', icon: 'history' },
]
</script>

<template>
  <nav class="tabbar" :class="{ contracted }" aria-label="Main">
    <template v-if="!contracted">
      <button
        v-for="t in TABS"
        :key="t.id"
        type="button"
        class="tab"
        :class="{ active: active === t.id }"
        :aria-current="active === t.id ? 'page' : undefined"
        @click="$emit('navigate', t.id)"
      >
        <AppIcon :name="t.icon" />
        <span>{{ t.label }}</span>
      </button>
    </template>
    <CrisisButton @open="$emit('crisis')" />
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 100%;
  max-width: 480px;
  height: var(--tabbar-h);
  display: flex;
  gap: 2px;
  padding: 6px 8px;
  background: var(--surface);
  border-top: 1px solid var(--line);
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  border: 0;
  border-radius: 12px;
  background: none;
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
}
.tab.active {
  background: var(--sage);
  color: var(--accent);
}
</style>
