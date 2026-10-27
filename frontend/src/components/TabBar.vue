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
        <span class="icon"><AppIcon :name="t.icon" /></span>
        <span>{{ t.label }}</span>
      </button>
    </template>
    <CrisisButton @open="$emit('crisis')" />
  </nav>
</template>

<style scoped>
/* A floating rounded pill, inset from the screen edges. */
.tabbar {
  position: fixed;
  bottom: var(--tabbar-gap);
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: calc(100% - var(--tabbar-gap) * 2);
  max-width: calc(480px - var(--tabbar-gap) * 2);
  height: var(--tabbar-h);
  display: flex;
  gap: 4px;
  padding: 6px 10px;
  background: var(--surface);
  border-radius: 999px;
  box-shadow: 0 6px 24px rgba(27, 39, 51, 0.12), 0 1px 3px rgba(27, 39, 51, 0.08);
}
.tabbar.contracted {
  width: auto;
  min-width: 140px;
}
.tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 4px;
  border: 0;
  border-radius: 999px;
  background: none;
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
}
.icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 30px;
  border-radius: 999px;
}
.tab.active {
  color: var(--accent);
}
.tab.active .icon {
  background: var(--secondary);
}
</style>
