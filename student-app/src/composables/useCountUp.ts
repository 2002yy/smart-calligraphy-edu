import { computed, onUnmounted, ref, watch } from "vue";

export function useCountUp(
  getter: () => number,
  duration = 300
) {
  const display = ref(0);
  let raf = 0;

  const stop = watch(
    computed(getter),
    (target, old) => {
      cancelAnimationFrame(raf);
      const from = old ?? 0;
      const start = performance.now();

      function tick(now: number) {
        const elapsed = now - start;
        const t = Math.min(elapsed / duration, 1);
        display.value = Math.round(from + (target - from) * t);
        if (t < 1) raf = requestAnimationFrame(tick);
      }

      raf = requestAnimationFrame(tick);
    },
    { immediate: true }
  );

  onUnmounted(() => {
    cancelAnimationFrame(raf);
    stop();
  });

  return display;
}
