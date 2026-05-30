<script setup lang="ts">
import { nextTick, onBeforeUnmount, onErrorCaptured, onMounted, ref } from "vue";

const hasError = ref(false);
const errorMessage = ref("页面渲染出现异常，请刷新后重试。");
const recoverKey = ref(0);

function setError(message?: string) {
  hasError.value = true;
  errorMessage.value = message || "页面渲染出现异常，请刷新后重试。";
}

function handleRuntimeError(event: Event) {
  const detail = (event as CustomEvent<{ message?: string }>).detail;
  setError(detail?.message);
}

async function resetError() {
  hasError.value = false;
  await nextTick();
  recoverKey.value++;
}

onErrorCaptured((error) => {
  const nextMessage = error instanceof Error ? error.message : "页面渲染出现异常，请刷新后重试。";
  setError(nextMessage);
  return false;
});

onMounted(() => {
  window.addEventListener("app-runtime-error", handleRuntimeError as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("app-runtime-error", handleRuntimeError as EventListener);
});
</script>

<template>
  <div v-if="hasError" class="error-shell">
    <div class="error-card">
      <div class="error-badge">运行时保护</div>
      <h2>学生端页面发生异常</h2>
      <p>{{ errorMessage }}</p>
      <div class="error-actions">
        <button class="error-btn" type="button" @click="resetError()">重试渲染</button>
        <button class="error-btn secondary" type="button" @click="window.location.reload()">刷新页面</button>
      </div>
    </div>
  </div>
  <template v-else>
    <slot :key="recoverKey" />
  </template>
</template>

<style scoped>
.error-shell {
  margin-top: 20px;
}

.error-card {
  display: grid;
  gap: 14px;
  padding: 28px;
  border-radius: 28px;
  border: 1px solid rgba(196, 75, 47, 0.18);
  background: linear-gradient(180deg, rgba(255, 244, 240, 0.96), rgba(255, 250, 247, 0.98));
  box-shadow: 0 18px 40px rgba(21, 66, 90, 0.12);
}

.error-badge {
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(196, 75, 47, 0.12);
  color: #9f371d;
  font-size: 12px;
}

.error-card h2,
.error-card p {
  margin: 0;
}

.error-card p {
  color: #7a5140;
  line-height: 1.8;
}

.error-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.error-btn {
  border: none;
  border-radius: 14px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #1572a1, #2b97ca);
  color: #ffffff;
}

.error-btn.secondary {
  background: rgba(255, 255, 255, 0.82);
  color: #17384a;
  border: 1px solid rgba(21, 66, 90, 0.12);
}
</style>
