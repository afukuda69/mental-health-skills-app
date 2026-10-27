<script setup>
import { CHECK_IN } from '../content/skills.js'

defineEmits(['answer'])
</script>

<template>
  <main class="screen">
    <h1>{{ CHECK_IN.prompt }}</h1>
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
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
