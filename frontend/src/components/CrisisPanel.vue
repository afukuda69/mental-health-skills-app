<script setup>
// Static panel: content is bundled from content/crisis.js. No fetch, no
// await, no backend or model, so it works with the backend stopped.
import { CRISIS } from '../content/crisis.js'

defineEmits(['close'])
</script>

<template>
  <div class="overlay" role="dialog" aria-modal="true" aria-labelledby="crisis-title" @keydown.esc="$emit('close')">
    <div class="panel" tabindex="-1">
      <h2 id="crisis-title">{{ CRISIS.title }}</h2>
      <p>{{ CRISIS.intro }}</p>
      <ul class="resources">
        <li v-for="r in CRISIS.resources" :key="r.name">
          <strong>{{ r.name }}</strong>
          <span class="detail">{{ r.detail }}</span>
          <span class="links">
            <a v-for="l in r.links" :key="l.href" :href="l.href">{{ l.label }}</a>
          </span>
        </li>
      </ul>
      <p v-for="n in CRISIS.notes" :key="n" class="note">{{ n }}</p>
      <button type="button" class="primary back-to-step" @click="$emit('close')">{{ CRISIS.back }}</button>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(40, 42, 44, 0.45);
}
.panel {
  width: 100%;
  max-width: 440px;
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  padding: 24px;
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
}
h2 {
  margin: 0 0 8px;
  font-size: 1.3rem;
}
.resources {
  list-style: none;
  padding: 0;
  margin: 16px 0;
}
.resources li {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}
.detail {
  color: var(--muted);
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.links a {
  color: var(--crisis-text);
  font-weight: 600;
}
.note {
  font-size: 0.9rem;
  color: var(--muted);
  margin: 4px 0;
}
.back-to-step {
  margin-top: 16px;
}
</style>
