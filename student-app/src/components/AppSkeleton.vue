<script setup lang="ts">
withDefaults(
  defineProps<{
    lines?: number;
    compact?: boolean;
  }>(),
  {
    lines: 3,
    compact: false
  }
);
</script>

<template>
  <div class="skeleton" :class="{ compact }" aria-hidden="true">
    <div class="skeleton-line title"></div>
    <div v-for="index in lines" :key="index" class="skeleton-line" :class="{ short: index === lines }"></div>
  </div>
</template>

<style scoped>
.skeleton {
  display: grid;
  gap: 10px;
}

.skeleton.compact {
  gap: 8px;
}

.skeleton-line {
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(76, 154, 204, 0.1) 25%, rgba(255, 255, 255, 0.86) 50%, rgba(76, 154, 204, 0.1) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.skeleton-line.title {
  width: 56%;
  height: 18px;
}

.skeleton-line.short {
  width: 68%;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}
</style>
