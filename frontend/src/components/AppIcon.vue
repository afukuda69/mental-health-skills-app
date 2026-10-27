<script setup>
// Simple stroke icons for the tab bar and cards. Decorative: always paired with a text label.
defineProps({ name: { type: String, required: true }, size: { type: Number, default: 22 } })

const PATHS = {
  home: 'M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z',
  history: 'M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zm-1 4h16M8 4v4m8-4v4',
  breath: 'M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16zm0 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8z',
  arrow: 'M5 12h14m-5-5l5 5l-5 5',
  chevron: 'M9 6l6 6l-6 6',
  back: 'M15 6l-6 6l6 6',
  clock: 'M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16zm0 4v4l3 2',
}
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="PATHS[name]" />
  </svg>
</template>
