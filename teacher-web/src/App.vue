<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import { storeToRefs } from "pinia";

import AppErrorBoundary from "./components/AppErrorBoundary.vue";
import FloatingToast from "./components/FloatingToast.vue";
import { useTeacherStore } from "./stores/teacher";

const route = useRoute();
const store = useTeacherStore();

const { loginForm, user, loading, message, noticeType, courses, classes, selectedCourseId, selectedClassId, activeClassName } =
  storeToRefs(store);

const navItems = [
  { to: "/dashboard", label: "教学看板", hint: "查看班级学习状态与统计数据" },
  { to: "/manage", label: "课程班级", hint: "创建课程与班级" },
  { to: "/tasks", label: "任务编排", hint: "发布书法训练任务" },
  { to: "/reviews", label: "批阅复盘", hint: "查看教师评语与复核结果" }
];

const currentNav = computed(() => navItems.find((item) => item.to === route.path) ?? navItems[0]);
const breadcrumbs = computed(() => ["教师端", "智慧书法", currentNav.value.label, activeClassName.value]);
const stageTitle = computed(() => {
  if (currentNav.value.to === "/dashboard") return "从课堂组织到结果复盘的教学闭环";
  if (currentNav.value.to === "/manage") return "先建课程，再建班级，把教学结构组织好";
  if (currentNav.value.to === "/tasks") return "把教学目标写进任务，让训练要求真正可执行";
  return "保留 AI 初评，也保留教师终评的专业判断";
});
const stageCopy = computed(() => {
  if (currentNav.value.to === "/dashboard") {
    return "这里是教学看板，展示班级的作业提交率、平均得分和共性问题，帮助教师快速掌握课堂整体情况。";
  }

  if (currentNav.value.to === "/manage") {
    return "在这里创建课程和班级，组织教学结构，管理学生。";
  }

  if (currentNav.value.to === "/tasks") {
    return "在这里发布训练任务，设置练习字、评分维度和截止时间，让学生明确练习目标。";
  }

  return "在这里查看 AI 初评结果，填写教师评语与复核分数，形成完整的教学反馈。";
});

const toastVisible = ref(false);
const toastTitle = computed(() =>
  noticeType.value === "error" ? "接口异常提示" : noticeType.value === "success" ? "操作反馈" : "系统通知"
);

watch(
  () => [message.value, noticeType.value] as const,
  ([nextMessage, nextType]) => {
    if (!nextMessage || nextMessage === "当前没有新的系统通知。") {
      toastVisible.value = false;
      return;
    }

    toastVisible.value = true;
    const timeout = nextType === "error" ? 5200 : 2800;
    window.clearTimeout((window as Window & { __teacherToastTimer?: number }).__teacherToastTimer);
    (window as Window & { __teacherToastTimer?: number }).__teacherToastTimer = window.setTimeout(() => {
      toastVisible.value = false;
    }, timeout);
  },
  { immediate: true }
);

onMounted(() => {
  store.restoreSession();
});
</script>

<template>
  <div class="shell">
    <FloatingToast :visible="toastVisible" :type="noticeType" :title="toastTitle" :message="message" />

    <aside class="sidebar">
      <div class="brand-rail">
        <p class="rail-en">SMART CALLIGRAPHY</p>
        <h1>智慧书法</h1>
        <p class="rail-role">教师教学中枢</p>
        <p class="rail-copy">
          智慧书法教学平台。教师端围绕”建课、建班、发任务、看评测、做复盘”组织完整教学流程。
        </p>
      </div>

      <section class="rail-section">
        <div class="section-head">
          <span>教师登录</span>
          <strong>{{ user ? "已连接" : "未连接" }}</strong>
        </div>
        <label class="field">
          <span>教师账号</span>
          <input v-model="loginForm.username" type="text" placeholder="teacher01" />
        </label>
        <label class="field">
          <span>登录密码</span>
          <input v-model="loginForm.password" type="password" placeholder="123456" />
        </label>
        <div class="rail-actions">
          <button class="primary-btn full" :disabled="loading" @click="store.login()">
            <span class="btn-content">
              <span v-if="loading" class="btn-spinner"></span>
              {{ loading ? "连接中..." : user ? "重新同步" : "连接后端" }}
            </span>
          </button>
          <button class="ghost-btn full" :disabled="!user" @click="store.logout()">退出登录</button>
        </div>
      </section>

      <section class="rail-section">
        <div class="section-head">
          <span>当前上下文</span>
          <strong>{{ user?.name || "等待登录" }}</strong>
        </div>
        <p class="rail-message" :class="noticeType">{{ message }}</p>

        <label class="field">
          <span>当前课程</span>
          <select
            :value="selectedCourseId ?? ''"
            @change="store.changeCourse(Number(($event.target as HTMLSelectElement).value) || null)"
          >
            <option value="">请选择课程</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>当前班级</span>
          <select
            :value="selectedClassId ?? ''"
            @change="store.changeClass(Number(($event.target as HTMLSelectElement).value) || null)"
          >
            <option value="">请选择班级</option>
            <option v-for="classItem in classes" :key="classItem.id" :value="classItem.id">
              {{ classItem.name }}
            </option>
          </select>
        </label>
      </section>

      <nav class="rail-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: route.path === item.to }"
        >
          <strong>{{ item.label }}</strong>
          <small>{{ item.hint }}</small>
        </RouterLink>
      </nav>
    </aside>

    <main class="workspace">
      <section class="stage">
        <div class="stage-copy">
          <p class="stage-brand">智慧书法</p>
          <h2>{{ stageTitle }}</h2>
          <p class="stage-text">{{ stageCopy }}</p>
          <div class="stage-actions">
            <RouterLink to="/manage" class="stage-link">进入课程班级</RouterLink>
            <RouterLink to="/tasks" class="stage-link secondary">继续任务编排</RouterLink>
          </div>
        </div>

        <div class="stage-meta">
          <p>当前模块</p>
          <strong>{{ currentNav.label }}</strong>
          <span>{{ activeClassName }}</span>
        </div>
      </section>

      <section class="workspace-topbar">
        <div class="breadcrumb-list">
          <span v-for="item in breadcrumbs" :key="item" class="breadcrumb-item">{{ item }}</span>
        </div>
        <div class="topbar-side">
          <span class="header-chip">{{ user?.name || "未登录" }}</span>
          <span class="header-chip warm">{{ activeClassName }}</span>
        </div>
      </section>

      <section class="notice-bar" :class="noticeType">
        <div class="notice-copy">
          <strong>{{ toastTitle }}</strong>
          <p>{{ message }}</p>
        </div>
        <button class="notice-close" type="button" @click="store.clearNotice()">收起</button>
      </section>

      <AppErrorBoundary>
        <RouterView />
      </AppErrorBoundary>
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 296px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  position: relative;
  overflow: hidden;
  padding: 22px 20px;
  border-right: 1px solid rgba(96, 54, 30, 0.16);
  background:
    linear-gradient(180deg, rgba(57, 31, 18, 0.98), rgba(42, 23, 13, 0.98)),
    radial-gradient(circle at top, rgba(198, 151, 98, 0.18), transparent 34%);
  color: #f8eee4;
}

.sidebar::before {
  content: "書";
  position: absolute;
  top: -10px;
  right: -16px;
  font-family: var(--font-display);
  font-size: 220px;
  line-height: 1;
  color: rgba(255, 232, 208, 0.06);
  transform: rotate(8deg);
  pointer-events: none;
}

.brand-rail {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 233, 212, 0.12);
}

.rail-en {
  margin: 0;
  color: rgba(231, 201, 162, 0.92);
  letter-spacing: 0.26em;
  font-size: 11px;
}

.brand-rail h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(34px, 3.5vw, 52px);
  line-height: 1.04;
  letter-spacing: 0.04em;
}

.rail-role {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  color: #f3d7ba;
}

.rail-copy {
  margin: 0;
  color: rgba(248, 238, 228, 0.78);
  line-height: 1.72;
  font-size: 14px;
}

.rail-section,
.rail-nav {
  position: relative;
  z-index: 1;
}

.rail-section {
  display: grid;
  gap: 10px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255, 233, 212, 0.1);
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.section-head span {
  font-size: 13px;
  color: rgba(248, 238, 228, 0.72);
}

.section-head strong {
  font-size: 13px;
  color: #f3d7ba;
}

.rail-actions {
  display: grid;
  gap: 10px;
  margin-top: 6px;
}

.rail-message {
  margin: 0;
  line-height: 1.75;
  color: rgba(248, 238, 228, 0.84);
}

.rail-message.success {
  color: #daf2cf;
}

.rail-message.error {
  color: #ffd0c4;
}

.rail-nav {
  display: grid;
  gap: 8px;
  padding-top: 16px;
}

.nav-link {
  position: relative;
  display: grid;
  gap: 4px;
  padding: 8px 0;
  text-decoration: none;
  color: #f8eee4;
  border-bottom: 1px solid rgba(255, 233, 212, 0.08);
  transition: transform 0.22s ease, color 0.22s ease;
}

.nav-link::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 0;
  height: 1px;
  background: linear-gradient(90deg, #f0cb9e, rgba(240, 203, 158, 0));
  transition: width 0.28s ease;
}

.nav-link strong {
  font-size: 16px;
}

.nav-link small {
  color: rgba(248, 238, 228, 0.64);
}

.nav-link:hover,
.nav-link.active {
  transform: translateX(4px);
  color: #fff7f0;
}

.nav-link:hover::after,
.nav-link.active::after {
  width: 100%;
}

.workspace {
  padding: 16px 20px 28px;
}

.stage {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 176px;
  align-items: end;
  min-height: 236px;
  padding: 24px 28px 22px;
  background:
    linear-gradient(120deg, rgba(255, 247, 236, 0.94), rgba(246, 228, 207, 0.92)),
    radial-gradient(circle at right top, rgba(168, 88, 50, 0.14), transparent 32%);
  border-radius: 26px;
  border: 1px solid rgba(78, 53, 34, 0.06);
  box-shadow: 0 18px 34px rgba(58, 35, 17, 0.08);
}

.stage::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.14), transparent 24%),
    repeating-linear-gradient(
      0deg,
      rgba(126, 71, 44, 0.04) 0,
      rgba(126, 71, 44, 0.04) 1px,
      transparent 1px,
      transparent 18px
    );
  opacity: 0.8;
  animation: paperShift 12s linear infinite;
}

.stage::after {
  content: "書";
  position: absolute;
  right: -80px;
  bottom: -8px;
  font-family: var(--font-display);
  font-size: clamp(180px, 20vw, 280px);
  line-height: 0.9;
  color: rgba(92, 46, 24, 0.1);
  animation: sealFloat 6.5s ease-in-out infinite;
}

.stage-copy,
.stage-meta {
  position: relative;
  z-index: 1;
}

.stage-copy {
  max-width: 680px;
}

.stage-brand {
  margin: 0 0 6px;
  font-family: var(--font-display);
  font-size: clamp(28px, 2.8vw, 44px);
  line-height: 1;
  color: #6d2f18;
  animation: stageFadeUp 0.7s ease both;
}

.stage h2 {
  margin: 0;
  max-width: 18ch;
  font-family: var(--font-display);
  font-size: clamp(22px, 2.2vw, 34px);
  line-height: 1.2;
  color: #2c1d15;
  animation: stageFadeUp 0.82s ease both;
}

.stage-text {
  margin: 12px 0 0;
  max-width: 36rem;
  font-size: 14px;
  line-height: 1.78;
  color: rgba(49, 34, 25, 0.76);
  animation: stageFadeUp 0.95s ease both;
}

.stage-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 16px;
  animation: stageFadeUp 1.08s ease both;
}

.stage-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 132px;
  padding: 10px 16px;
  text-decoration: none;
  border-radius: 999px;
  background: #6d2f18;
  color: #fff8f1;
  transition: transform 0.2s ease, background 0.2s ease;
}

.stage-link.secondary {
  background: rgba(109, 47, 24, 0.1);
  color: #6d2f18;
}

.stage-link:hover {
  transform: translateY(-1px);
}

.stage-meta {
  justify-self: end;
  display: grid;
  gap: 4px;
  text-align: right;
  animation: stageFloatIn 1.05s ease both;
}

.stage-meta p,
.stage-meta span {
  margin: 0;
  font-size: 13px;
  color: rgba(79, 52, 38, 0.68);
}

.stage-meta strong {
  font-family: var(--font-display);
  font-size: 22px;
  color: #47281b;
}

.workspace-topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 12px 2px 6px;
}

.breadcrumb-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.breadcrumb-item {
  position: relative;
  padding-right: 16px;
  font-size: 13px;
  color: var(--muted);
}

.breadcrumb-item:not(:last-child)::after {
  content: "/";
  position: absolute;
  right: 4px;
  color: rgba(123, 44, 23, 0.38);
}

.topbar-side {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.header-chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(166, 72, 46, 0.08);
  color: var(--accent-deep);
  font-size: 13px;
}

.header-chip.warm {
  background: rgba(200, 169, 107, 0.2);
}

.notice-bar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 14px 0 18px;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.notice-copy {
  display: grid;
  gap: 6px;
}

.notice-copy strong {
  font-size: 16px;
}

.notice-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.notice-close {
  border: none;
  background: transparent;
  color: var(--accent-deep);
}

.btn-content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  animation: spin 0.8s linear infinite;
}

.full {
  width: 100%;
}

@media (max-width: 1320px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .stage {
    grid-template-columns: 1fr;
    min-height: 236px;
  }

  .stage-meta {
    justify-self: start;
    text-align: left;
    margin-top: 18px;
  }
}

@media (max-width: 720px) {
  .workspace {
    padding: 14px 16px 24px;
  }

  .sidebar {
    padding: 18px 16px;
  }

  .stage {
    padding: 22px 18px;
  }

  .workspace-topbar,
  .notice-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@keyframes stageFadeUp {
  from {
    opacity: 0;
    transform: translateY(18px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes stageFloatIn {
  from {
    opacity: 0;
    transform: translateX(16px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes paperShift {
  from {
    transform: translateX(0);
  }

  50% {
    transform: translateX(-10px);
  }

  to {
    transform: translateX(0);
  }
}

@keyframes sealFloat {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-8px);
  }
}
</style>
