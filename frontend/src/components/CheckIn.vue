<script setup>
import { CHECK_IN } from '../content/skills.js'

defineEmits(['answer'])
</script>

<template>
  <main class="screen">
    <div class="card">
      <h1>{{ CHECK_IN.prompt }}</h1>
      <div class="options">
        <button v-for="o in CHECK_IN.options" :key="o.label" type="button" @click="$emit('answer', o.key)">
          {{ o.label }}
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
h1 {
  font-size: 1.6rem;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
