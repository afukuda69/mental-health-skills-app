<script setup>
// Wraps every exercise step: the step plus Stop exercise. Crisis support is
// rendered by App.vue, so it stays visible here too. No navigation, no
// history link, no progress bar (design.md section c).
import { BUTTONS } from '../content/skills.js'

defineEmits(['stop'])
</script>

<template>
  <div class="frame">
    <button type="button" class="stop" @click="$emit('stop')">{{ BUTTONS.stopExercise }}</button>
    <div class="step">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.frame {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.stop {
  position: fixed;
  top: 12px;
  left: 16px;
  z-index: 100;
}
.step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 72px 16px 32px;
  text-align: center;
}
</style>
