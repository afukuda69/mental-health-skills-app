<script setup>
// Shared header for an exercise: the skill name and one line. No navigation,
// no history link, no progress bar inside the exercise (design.md section c, D1).
// The skill renders its own one-tap Stop exercise next to its controls. While
// it runs, the tab bar contracts to the Crisis tab alone (App.vue).
import PageHeader from './PageHeader.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <main class="screen narrow exercise">
    <PageHeader :title="title" :subtitle="subtitle" />
    <slot />
  </main>
</template>
