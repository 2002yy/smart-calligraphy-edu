<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

const props = withDefaults(
  defineProps<{
    score: number;
    label: string;
    size?: number;
    strokeWidth?: number;
    delay?: number;
    max?: number;
  }>(),
  { size: 80, strokeWidth: 6, delay: 0, max: 10 }
);

const radius = (props.size - props.strokeWidth) / 2;
const circumference = 2 * Math.PI * radius;
const center = props.size / 2;

const animatedOffset = ref(circumference);
const visible = ref(false);

const pct = computed(() => (props.max > 0 ? (Math.min(props.max, Math.max(0, props.score)) / props.max) * 100 : 0));

const dashOffset = computed(() => circumference - (pct.value / 100) * circumference);

const ringColor = computed(() => {
  if (pct.value < 60) return "#c44b2f";
  if (pct.value < 80) return "#d49a3a";
  return "#2b97ca";
});

const trackColor = computed(() => {
  if (pct.value < 60) return "rgba(196, 75, 47, 0.12)";
  if (pct.value < 80) return "rgba(212, 154, 58, 0.12)";
  return "rgba(43, 151, 202, 0.12)";
});

onMounted(async () => {
  await nextTick();
  if (props.delay > 0) {
    await new Promise((r) => setTimeout(r, props.delay));
  }
  visible.value = true;
  animatedOffset.value = dashOffset.value;
});
</script>

<template>
  <div class="score-ring-wrap" :class="{ visible }">
    <svg :width="size" :height="size" class="score-ring-svg">
      <circle
        :cx="center" :cy="center" :r="radius"
        :stroke="trackColor" :stroke-width="strokeWidth"
        fill="none"
      />
      <g :transform="`rotate(-90, ${center}, ${center})`">
        <circle
          :cx="center" :cy="center" :r="radius"
          :stroke="ringColor" :stroke-width="strokeWidth"
          fill="none" stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="animatedOffset"
          class="ring-fill"
        />
      </g>
    </svg>
    <div class="ring-center">
      <strong class="ring-score" :style="{ color: ringColor }">{{ score }}</strong>
      <span class="ring-label">{{ label }}</span>
    </div>
  </div>
</template>

<style scoped>
.score-ring-wrap {
  position: relative;
  display: inline-grid;
  place-items: center;
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.score-ring-wrap.visible {
  opacity: 1;
  transform: scale(1);
}

.score-ring-svg {
  display: block;
}

.ring-fill {
  transition: stroke-dashoffset 0.9s cubic-bezier(0.34, 1.2, 0.64, 1);
}

.ring-center {
  position: absolute;
  display: grid;
  gap: 1px;
  text-align: center;
  pointer-events: none;
}

.ring-score {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  transition: color 0.3s ease;
  font-variant-numeric: tabular-nums;
}

.ring-label {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.2;
}
</style>
