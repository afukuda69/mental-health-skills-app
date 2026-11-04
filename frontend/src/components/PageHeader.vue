<script setup>
// The same header on every main screen: a title and a one-line subtitle.
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <header class="page-header">
    <h1>{{ title }}</h1>
    <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
  </header>
</template>

<style scoped>
.page-header {
  margin-bottom: var(--space-5);
}
h1 {
  margin: 0;
}
.subtitle {
  margin: var(--space-1) 0 0;
  color: var(--muted);
  font-size: var(--fs-lg);
}
</style>
