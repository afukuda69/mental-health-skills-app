<script setup>
// Bottom navigation: Home, Activities, Chat, Profile (with History inside), Crisis. The Crisis tab is CrisisButton,
// which imports only static content, so it works with the backend down.
// While an exercise runs, the bar contracts to the Crisis tab alone (D1).
import { APP_NAME } from '../content/skills.js'
import CrisisButton from './CrisisButton.vue'

defineProps({
  active: { type: String, default: null },
  contracted: { type: Boolean, default: false },
})
defineEmits(['navigate', 'crisis'])

const TABS = [
  { id: 'home', label: 'Home', icon: 'home' },
  { id: 'activities', label: 'Activities', icon: 'activities' },
  { id: 'chat', label: 'Chat', icon: 'chat' },
  { id: 'profile', label: 'Profile', icon: 'profile' },
]
</script>

<template>
  <nav class="tabbar" :class="{ contracted }" aria-label="Main">
    <span class="brand" aria-hidden="true">{{ APP_NAME }}</span>
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
        <!-- Text labels only, no icons. -->
        <span class="name">{{ t.label }}</span>
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
  width: 44px;
  height: 30px;
  border-radius: 999px;
}
.tab.active {
  color: var(--accent);
}
.tab {
  justify-content: center;
}
.name {
  font-size: 0.9rem;
}
.tab.active {
  background: var(--secondary);
}
.brand {
  display: none;
}

/* Wide screens: a full-width top navigation bar instead of the floating pill. */
@media (min-width: 900px) {
  .tabbar,
  .tabbar.contracted {
    top: 0;
    bottom: auto;
    left: 0;
    transform: none;
    width: 100%;
    max-width: none;
    min-width: 0;
    height: var(--tabbar-h);
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    padding: 0 40px;
    border-radius: 0;
    box-shadow: 0 1px 0 var(--line), 0 2px 10px rgba(27, 39, 51, 0.05);
  }
  .brand {
    display: block;
    margin-right: auto;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
  }
  .tab {
    flex: none;
    flex-direction: row;
    gap: 6px;
    padding: 8px 14px;
    font-size: 0.95rem;
  }
  .tab .icon {
    width: auto;
    height: auto;
    background: none;
  }
  .tab.active {
    background: var(--secondary);
  }
  .tab.active .icon {
    background: none;
  }
  /* Show every label on wide screens (narrow screens show only the active one). */
  .tab .sr,
  .tab .name {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    clip: auto;
    font-size: 0.95rem;
  }
  .tabbar :deep(.crisis-button) {
    flex: none;
    flex-direction: row;
    gap: 6px;
    margin-left: 8px;
    padding: 8px 16px;
    background: var(--crisis-bg);
    font-size: 0.95rem;
  }
}
</style>
