<script setup lang="ts">
import { onMounted, ref } from "vue";

const props = withDefaults(defineProps<{
  storageKey?: string;
}>(), { storageKey: "intro-collapsed" });

const collapsed = ref(true);

onMounted(() => {
  const visited = sessionStorage.getItem(props.storageKey);
  if (!visited) {
    collapsed.value = false;
    sessionStorage.setItem(props.storageKey, "1");
  }
});

function toggle() {
  collapsed.value = !collapsed.value;
}
</script>

<template>
  <section class="intro-block" :class="{ 'intro-collapsed': collapsed }">
    <button class="intro-head" type="button" @click="toggle">
      <strong>页面说明</strong>
      <span class="intro-arrow">{{ collapsed ? "展开" : "收起" }}</span>
    </button>
    <div v-show="!collapsed" class="intro-body">
      <p><slot /></p>
    </div>
  </section>
</template>

<style scoped>
.intro-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.intro-head strong {
  font-size: 15px;
}

.intro-arrow {
  font-size: 12px;
  color: var(--muted);
  transition: color 0.15s ease;
}

.intro-head:hover .intro-arrow {
  color: var(--accent);
}

.intro-body {
  overflow: hidden;
  transition: max-height 0.25s ease;
}

.intro-body p {
  margin: 8px 0 0;
  max-width: 62rem;
  color: var(--muted);
  line-height: 1.8;
}
</style>
