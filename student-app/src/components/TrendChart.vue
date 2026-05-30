<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    scores: number[];
    labels?: string[];
    width?: number;
    height?: number;
  }>(),
  { width: 260, height: 80, labels: () => [] }
);

const padding = { top: 12, right: 12, bottom: 24, left: 12 };
const chartW = props.width - padding.left - padding.right;
const chartH = props.height - padding.top - padding.bottom;

const points = computed(() => {
  const n = props.scores.length;
  if (n < 2) return [];
  const min = Math.min(...props.scores);
  const max = Math.max(...props.scores);
  const range = max - min || 1;
  return props.scores.map((s, i) => ({
    x: padding.left + (i / (n - 1)) * chartW,
    y: padding.top + chartH - ((s - min) / range) * (chartH - 8),
    score: s,
  }));
});

const pathD = computed(() => {
  if (points.value.length < 2) return "";
  return points.value
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");
});

const areaD = computed(() => {
  if (points.value.length < 2) return "";
  const first = points.value[0];
  const last = points.value[points.value.length - 1];
  const bottomY = padding.top + chartH;
  return `${pathD.value} L${last.x.toFixed(1)},${bottomY} L${first.x.toFixed(1)},${bottomY} Z`;
});

const trend = computed<"up" | "stable" | "down">(() => {
  const n = props.scores.length;
  if (n < 2) return "stable";
  const first = props.scores[0];
  const last = props.scores[n - 1];
  const diff = last - first;
  if (diff > 3) return "up";
  if (diff < -3) return "down";
  return "stable";
});

const trendLabel = computed(() => {
  const map = { up: "稳定上升", stable: "波动平稳", down: "持续下降" };
  return map[trend.value];
});
</script>

<template>
  <div class="trend-chart-wrap">
    <svg :width="width" :height="height" class="trend-svg" v-if="scores.length >= 2">
      <defs>
        <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.2" />
          <stop offset="100%" stop-color="var(--accent)" stop-opacity="0.02" />
        </linearGradient>
      </defs>

      <path :d="areaD" fill="url(#area-grad)" />

      <path :d="pathD" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="trend-line" />

      <circle
        v-for="(p, i) in points"
        :key="i"
        :cx="p.x"
        :cy="p.y"
        r="3.5"
        fill="var(--accent)"
        stroke="#fff"
        stroke-width="1.5"
        class="trend-dot"
      />

      <text
        v-for="(p, i) in points"
        :key="`label-${i}`"
        :x="p.x"
        y="0"
        dy="76"
        text-anchor="middle"
        class="trend-label"
      >
        {{ labels[i] || p.score }}
      </text>
    </svg>

    <div v-else class="trend-placeholder">
      <span>至少需要 2 次评测记录</span>
    </div>

    <span class="trend-tag" :class="trend">
      {{ trendLabel }}
    </span>
  </div>
</template>

<style scoped>
.trend-chart-wrap {
  display: grid;
  gap: 10px;
}

.trend-svg {
  display: block;
  overflow: visible;
}

.trend-line {
  filter: drop-shadow(0 1px 3px rgba(43, 151, 202, 0.2));
}

.trend-dot {
  transition: r 0.15s ease;
}

.trend-dot:hover {
  r: 5.5;
}

.trend-label {
  font-size: 10px;
  fill: var(--muted);
  font-family: inherit;
}

.trend-placeholder {
  display: grid;
  place-items: center;
  min-height: 60px;
  color: var(--muted);
  font-size: 13px;
}

.trend-tag {
  display: inline-block;
  width: fit-content;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
}

.trend-tag.up {
  background: rgba(43, 151, 202, 0.12);
  color: #1a7aa8;
}

.trend-tag.stable {
  background: rgba(212, 154, 58, 0.12);
  color: #b0882e;
}

.trend-tag.down {
  background: rgba(196, 75, 47, 0.12);
  color: #a83a1a;
}
</style>
