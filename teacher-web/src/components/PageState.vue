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
    <div class="empty-icon">书</div>
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
  border: 1px dashed rgba(78, 53, 34, 0.14);
  background:
    linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(249, 242, 234, 0.92)),
    radial-gradient(circle at top, rgba(200, 169, 107, 0.08), transparent 60%);
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
  background: rgba(166, 72, 46, 0.1);
  color: var(--accent-deep);
  font-size: 12px;
}

.empty-icon {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(166, 72, 46, 0.08);
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
  background: linear-gradient(90deg, rgba(226, 206, 188, 0.5), rgba(255, 255, 255, 0.9), rgba(226, 206, 188, 0.5));
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
