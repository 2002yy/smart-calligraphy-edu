<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import { storeToRefs } from "pinia";

import AppErrorBoundary from "./components/AppErrorBoundary.vue";
import FloatingToast from "./components/FloatingToast.vue";
import { useStudentStore } from "./stores/student";

const route = useRoute();
const store = useStudentStore();

const { loginForm, user, loading, joining, message, noticeType, classes, selectedClassId, joinForm } = storeToRefs(store);

const navItems = [
  { to: "/overview", label: "学习总览", hint: "看当前学习状态" },
  { to: "/tasks", label: "任务中心", hint: "查看本周训练任务" },
  { to: "/submit", label: "提交评测", hint: "上传作业并触发评测" },
  { to: "/growth", label: "成长档案", hint: "查看个人成长数据" }
];

const currentNav = computed(() => navItems.find((item) => item.to === route.path) ?? navItems[0]);
const breadcrumbs = computed(() => ["学生端", "智慧书法", currentNav.value.label]);
const stageTitle = computed(() => {
  if (currentNav.value.to === "/overview") return "从领任务到看反馈，一条学习链路一次讲清";
  if (currentNav.value.to === "/tasks") return "先知道练什么，再知道为什么练";
  if (currentNav.value.to === "/submit") return "把作品提交与 AI 评测放进同一条动作链";
  return "把每一次练习，沉淀成看得见的成长";
});
const stageCopy = computed(() => {
  if (currentNav.value.to === "/overview") {
    return "学生端不是信息堆砌页面，而是围绕练习目标、提交动作、智能反馈和成长沉淀组织的一条真实学习路径。";
  }

  if (currentNav.value.to === "/tasks") {
    return "任务中心负责把教师要求转成学生能理解、能执行的训练目标，让练习字、评分维度和截止时间一目了然。";
  }

  if (currentNav.value.to === "/submit") {
    return "学生上传书法作品后，直接触发 AI 评测，评测结果即时回传到学习记录与教师端。";
  }

  return "成长档案记录平均得分、问题标签和练习建议，帮助学生跟踪自己的学习进步。";
});

const toastVisible = ref(false);
const toastTitle = computed(() =>
  noticeType.value === "error" ? "接口异常提示" : noticeType.value === "success" ? "学习反馈" : "系统通知"
);

watch(
  () => [message.value, noticeType.value] as const,
  ([nextMessage, nextType]) => {
    if (!nextMessage || nextMessage === "当前没有新的学习通知。") {
      toastVisible.value = false;
      return;
    }

    toastVisible.value = true;
    const timeout = nextType === "error" ? 5200 : 2800;
    window.clearTimeout((window as Window & { __studentToastTimer?: number }).__studentToastTimer);
    (window as Window & { __studentToastTimer?: number }).__studentToastTimer = window.setTimeout(() => {
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
        <p class="rail-role">学生学习空间</p>
        <p class="rail-copy">
          围绕”领任务、交作品、看反馈、记成长”组织完整学习体验，让每一次练习都有反馈。
        </p>
      </div>

      <section class="rail-section">
        <div class="section-head">
          <span>学生登录</span>
          <strong>{{ user ? "已连接" : "未连接" }}</strong>
        </div>
        <label class="field">
          <span>学生账号</span>
          <input v-model="loginForm.username" type="text" placeholder="student01" />
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
          <span>加入班级</span>
          <strong>{{ classes.length }} 个班级</strong>
        </div>
        <p class="rail-message" :class="noticeType">{{ message }}</p>

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

        <label class="field">
          <span>班级邀请码</span>
          <input v-model="joinForm.inviteCode" type="text" placeholder="CALLI2026" />
        </label>

        <button class="primary-btn full" :disabled="joining" @click="store.joinClass()">
          <span class="btn-content">
            <span v-if="joining" class="btn-spinner"></span>
            {{ joining ? "加入中..." : "加入班级" }}
          </span>
        </button>
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
            <RouterLink to="/tasks" class="stage-link">进入任务中心</RouterLink>
            <RouterLink to="/submit" class="stage-link secondary">继续提交评测</RouterLink>
          </div>
        </div>

        <div class="stage-meta">
          <p>当前模块</p>
          <strong>{{ currentNav.label }}</strong>
          <span>{{ user?.name || "等待登录" }}</span>
        </div>
      </section>

      <section class="workspace-topbar">
        <div class="breadcrumb-list">
          <span v-for="item in breadcrumbs" :key="item" class="breadcrumb-item">{{ item }}</span>
        </div>
        <div class="topbar-side">
          <span class="header-chip">{{ user?.name || "未登录" }}</span>
          <span class="header-chip cool">{{ classes.length }} 个班级</span>
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
  border-right: 1px solid rgba(23, 56, 74, 0.14);
  background:
    linear-gradient(180deg, rgba(10, 46, 64, 0.98), rgba(7, 35, 49, 0.98)),
    radial-gradient(circle at top, rgba(92, 191, 236, 0.18), transparent 34%);
  color: #edf8ff;
}

.sidebar::before {
  content: "墨";
  position: absolute;
  top: -8px;
  right: -10px;
  font-family: var(--font-display);
  font-size: 216px;
  line-height: 1;
  color: rgba(219, 242, 255, 0.06);
  transform: rotate(10deg);
  pointer-events: none;
}

.brand-rail {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(209, 236, 255, 0.12);
}

.rail-en {
  margin: 0;
  color: rgba(169, 228, 255, 0.92);
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
  color: #d4f1ff;
}

.rail-copy {
  margin: 0;
  color: rgba(237, 248, 255, 0.78);
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
  border-bottom: 1px solid rgba(209, 236, 255, 0.1);
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.section-head span {
  font-size: 13px;
  color: rgba(237, 248, 255, 0.72);
}

.section-head strong {
  font-size: 13px;
  color: #c8edff;
}

.rail-actions {
  display: grid;
  gap: 10px;
  margin-top: 6px;
}

.rail-message {
  margin: 0;
  line-height: 1.75;
  color: rgba(237, 248, 255, 0.84);
}

.rail-message.success {
  color: #ddffe9;
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
  color: #edf8ff;
  border-bottom: 1px solid rgba(209, 236, 255, 0.08);
  transition: transform 0.22s ease, color 0.22s ease;
}

.nav-link::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 0;
  height: 1px;
  background: linear-gradient(90deg, #9edfff, rgba(158, 223, 255, 0));
  transition: width 0.28s ease;
}

.nav-link strong {
  font-size: 16px;
}

.nav-link small {
  color: rgba(237, 248, 255, 0.64);
}

.nav-link:hover,
.nav-link.active {
  transform: translateX(4px);
  color: #ffffff;
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
    linear-gradient(120deg, rgba(246, 252, 255, 0.96), rgba(220, 241, 252, 0.92)),
    radial-gradient(circle at right top, rgba(75, 154, 204, 0.16), transparent 32%);
  border-radius: 26px;
  border: 1px solid rgba(21, 66, 90, 0.06);
  box-shadow: 0 18px 34px rgba(21, 66, 90, 0.08);
}

.stage::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.14), transparent 22%),
    repeating-linear-gradient(
      0deg,
      rgba(33, 92, 121, 0.04) 0,
      rgba(33, 92, 121, 0.04) 1px,
      transparent 1px,
      transparent 18px
    );
  opacity: 0.82;
  animation: paperShift 12s linear infinite;
}

.stage::after {
  content: "墨";
  position: absolute;
  right: 24px;
  bottom: -8px;
  font-family: var(--font-display);
  font-size: clamp(132px, 15vw, 190px);
  line-height: 0.9;
  color: rgba(19, 85, 119, 0.1);
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
  color: #11516f;
  animation: stageFadeUp 0.7s ease both;
}

.stage h2 {
  margin: 0;
  max-width: 7ch;
  font-family: var(--font-display);
  font-size: clamp(22px, 2.2vw, 34px);
  line-height: 1.2;
  color: #17384a;
  animation: stageFadeUp 0.82s ease both;
}

.stage-text {
  margin: 12px 0 0;
  max-width: 36rem;
  font-size: 14px;
  line-height: 1.78;
  color: rgba(23, 56, 74, 0.76);
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
  background: #11516f;
  color: #f6fdff;
  transition: transform 0.2s ease, background 0.2s ease;
}

.stage-link.secondary {
  background: rgba(17, 81, 111, 0.1);
  color: #11516f;
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
  color: rgba(23, 56, 74, 0.66);
}

.stage-meta strong {
  font-family: var(--font-display);
  font-size: 22px;
  color: #17384a;
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
  color: rgba(15, 78, 113, 0.38);
}

.topbar-side {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.header-chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(76, 154, 204, 0.12);
  color: var(--accent-deep);
  font-size: 13px;
}

.header-chip.cool {
  background: rgba(140, 214, 255, 0.24);
}

.notice-bar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 14px 0 18px;
  border-bottom: 1px solid rgba(21, 66, 90, 0.1);
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
