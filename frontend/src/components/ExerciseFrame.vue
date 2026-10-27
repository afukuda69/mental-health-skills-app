<script setup>
// Shared header for the exercise: the skill name only. No navigation, no
// history link, no progress bar inside the exercise (design.md section c, D1).
// The skill renders its own one-tap Stop exercise next to its controls. While
// it runs, the tab bar contracts to the Crisis tab alone (App.vue).
defineProps({ title: { type: String, required: true } })
</script>

<template>
  <main class="screen exercise">
    <h1>{{ title }}</h1>
    <slot />
  </main>
</template>
