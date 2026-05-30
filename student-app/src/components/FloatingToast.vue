<script setup lang="ts">
defineProps<{
  visible: boolean;
  type: "info" | "success" | "error";
  title: string;
  message: string;
}>();
</script>

<template>
  <transition name="toast-fade">
    <div v-if="visible" class="toast-shell" :class="type">
      <div class="toast-dot"></div>
      <div class="toast-copy">
        <strong>{{ title }}</strong>
        <p>{{ message }}</p>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.toast-shell {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 40;
  width: min(360px, calc(100vw - 32px));
  display: flex;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid transparent;
  box-shadow: 0 18px 40px rgba(21, 66, 90, 0.16);
}

.toast-shell.info {
  background: rgba(244, 251, 255, 0.98);
  border-color: rgba(76, 154, 204, 0.18);
}

.toast-shell.success {
  background: rgba(241, 251, 245, 0.98);
  border-color: rgba(72, 165, 110, 0.16);
}

.toast-shell.error {
  background: rgba(255, 241, 238, 0.98);
  border-color: rgba(196, 75, 47, 0.18);
}

.toast-dot {
  width: 10px;
  height: 10px;
  margin-top: 7px;
  border-radius: 999px;
  background: currentColor;
}

.toast-shell.info .toast-dot {
  color: #2b97ca;
}

.toast-shell.success .toast-dot {
  color: #48a56e;
}

.toast-shell.error .toast-dot {
  color: #c44b2f;
}

.toast-copy {
  display: grid;
  gap: 4px;
}

.toast-copy strong,
.toast-copy p {
  margin: 0;
}

.toast-copy p {
  line-height: 1.7;
  color: #4e6b7b;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.22s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
