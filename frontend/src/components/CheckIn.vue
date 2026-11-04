<script setup>
import { CHECK_IN } from '../content/skills.js'
import PageHeader from './PageHeader.vue'

defineEmits(['answer'])
</script>

<template>
  <main class="screen narrow">
    <PageHeader :title="CHECK_IN.prompt" :subtitle="CHECK_IN.note" />
    <div class="options">
      <button v-for="o in CHECK_IN.options" :key="o.label" type="button" @click="$emit('answer', o.key)">
        {{ o.label }}
      </button>
    </div>
  </main>
</template>

<style scoped>
.options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>
