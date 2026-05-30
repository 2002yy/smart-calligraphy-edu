<script setup lang="ts">
defineProps<{
  mode: "loading" | "empty";
  title: string;
  description: string;
  compact?: boolean;
}>();
</script>

<template>
  <div v-if="mode === 'loading'" class="state-card loading">
    <div class="state-header">
      <span class="state-tag">数据同步中</span>
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
    <div class="skeleton-grid" :class="{ compact }">
      <div v-for="index in compact ? 3 : 6" :key="index" class="skeleton-item">
        <span class="skeleton-line short"></span>
        <span class="skeleton-line"></span>
        <span class="skeleton-line light"></span>
      </div>
    </div>
  </div>

  <div v-else class="state-card empty">
    <div class="empty-icon">习</div>
    <div class="state-header">
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
  </div>
</template>

<style scoped>
.state-card {
  display: grid;
  gap: 16px;
  padding: 24px;
  border-radius: 22px;
  border: 1px dashed rgba(21, 66, 90, 0.14);
  background:
    linear-gradient(180deg, rgba(252, 254, 255, 0.98), rgba(241, 250, 255, 0.92)),
    radial-gradient(circle at top, rgba(102, 179, 222, 0.08), transparent 60%);
}

.state-card.empty {
  place-items: center;
  min-height: 180px;
  text-align: center;
}

.state-header {
  display: grid;
  gap: 8px;
}

.state-header strong {
  font-size: 20px;
}

.state-header p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.state-tag {
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(76, 154, 204, 0.12);
  color: var(--accent-deep);
  font-size: 12px;
}

.empty-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(76, 154, 204, 0.08);
  color: var(--accent-deep);
  font-family: "STKaiti", "KaiTi", sans-serif;
  font-size: 24px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.skeleton-grid.compact {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.skeleton-item {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
}

.skeleton-line {
  display: block;
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(190, 223, 240, 0.55), rgba(255, 255, 255, 0.9), rgba(190, 223, 240, 0.55));
  background-size: 240% 100%;
  animation: shimmer 1.5s linear infinite;
}

.skeleton-line.short {
  width: 45%;
}

.skeleton-line.light {
  width: 72%;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -40% 0;
  }
}

@media (max-width: 1280px) {
  .skeleton-grid,
  .skeleton-grid.compact {
    grid-template-columns: 1fr;
  }
}
</style>
