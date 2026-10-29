<script setup>
// Simple stroke icons for the tab bar and cards. Decorative: always paired with a text label.
defineProps({ name: { type: String, required: true }, size: { type: Number, default: 22 } })

const PATHS = {
  home: 'M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z',
  activities: 'M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zm0 4a5 5 0 1 0 0 10a5 5 0 1 0 0-10zm0 3a2 2 0 1 0 0 4a2 2 0 1 0 0-4z',
  chat: 'M5 5h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H10l-4 3v-3H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm4 5h6m-6 3h4',
  history: 'M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zm-1 4h16M8 4v4m8-4v4',
  breath: 'M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16zm0 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8z',
  pause: 'M12 3l7 3v5c0 4.5-3 8-7 10c-4-2-7-5.5-7-10V6zM9 12h6',
  spark: 'M12 4v4m0 8v4M4 12h4m8 0h4M7 7l2 2m6 6l2 2M17 7l-2 2m-6 6l-2 2',
  arrow: 'M5 12h14m-5-5l5 5l-5 5',
  chevron: 'M9 6l6 6l-6 6',
  back: 'M15 6l-6 6l6 6',
  profile: 'M12 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8zM5 20c0-3.5 3-6 7-6s7 2.5 7 6',
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
