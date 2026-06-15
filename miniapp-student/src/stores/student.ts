import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { mobileApi } from "../api/mobile";
import { API_BASE_URL, TOKEN_KEY } from "../api/request";
import type { CurrentUser, Growth, Homework, MobileResult, StudentTask } from "../types";

type Stage = "idle" | "uploading" | "evaluating" | "finished" | "failed";

function absoluteUrl(path?: string | null) {
  if (!path) return "";
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path}`;
}

export const useStudentStore = defineStore("student", () => {
  const username = ref("student01");
  const password = ref("123456");
  const token = ref<string>(uni.getStorageSync(TOKEN_KEY) || "");
  const user = ref<CurrentUser | null>(null);
  const tasks = ref<StudentTask[]>([]);
  const selectedTask = ref<StudentTask | null>(null);
  const latestHomework = ref<Homework | null>(null);
  const latestResult = ref<MobileResult | null>(null);
  const history = ref<Homework[]>([]);
  const progress = ref<Growth | null>(null);
  const stage = ref<Stage>("idle");
  const loading = ref(false);
  const message = ref("登录后查看今日练习任务。");

  const todayTask = computed(() => tasks.value[0] || null);
  const avgScore = computed(() => Math.round((progress.value?.avg_score || 0) * 10));
  const resultImage = computed(() => absoluteUrl(latestResult.value?.image_url || latestHomework.value?.image_url));

  function setMessage(next: string) {
    message.value = next;
  }

  async function login() {
    loading.value = true;
    try {
      const response = await mobileApi.login(username.value, password.value);
      token.value = response.access_token;
      user.value = response.user;
      uni.setStorageSync(TOKEN_KEY, response.access_token);
      await refresh();
      uni.switchTab({ url: "/pages/home/index" });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "登录失败，请检查账号和后端服务。");
    } finally {
      loading.value = false;
    }
  }

  async function restoreSession() {
    if (!token.value) {
      uni.reLaunch({ url: "/pages/login/index" });
      return;
    }
    try {
      user.value = await mobileApi.getCurrentUser();
      await refresh();
    } catch {
      logout();
    }
  }

  async function refresh() {
    const [taskData, progressData, historyData] = await Promise.all([
      mobileApi.getTasks(),
      mobileApi.getProgress(),
      mobileApi.getHistory()
    ]);
    tasks.value = taskData;
    selectedTask.value = selectedTask.value || taskData[0] || null;
    progress.value = progressData;
    history.value = historyData;
    setMessage(taskData.length ? "今日练习已同步，可以开始上传作品。" : "暂时没有新的练习任务。");
  }

  async function openTask(taskId: number) {
    await loadTask(taskId);
    uni.navigateTo({ url: `/pages/task/detail?id=${taskId}` });
  }

  async function loadTask(taskId: number) {
    selectedTask.value = await mobileApi.getTask(taskId);
  }

  async function submitAndEvaluate(filePath: string) {
    if (!selectedTask.value) {
      setMessage("请先选择一个练习任务。");
      return;
    }
    stage.value = "uploading";
    try {
      latestHomework.value = await mobileApi.submitHomework(selectedTask.value.id, filePath);
      stage.value = "evaluating";
      await mobileApi.startEvaluation(latestHomework.value.id, "auto");
      latestResult.value = await waitForResult(latestHomework.value.id);
      stage.value = "finished";
      await refresh();
      uni.navigateTo({ url: `/pages/result/index?id=${latestHomework.value.id}` });
    } catch (error) {
      stage.value = "failed";
      setMessage(error instanceof Error ? error.message : "上传或评分失败，请稍后重试。");
    }
  }

  async function waitForResult(homeworkId: number, maxRetries = 30) {
    for (let index = 0; index < maxRetries; index += 1) {
      try {
        const result = await mobileApi.getResult(homeworkId);
        if (result.status === "finished") return result;
      } catch (error) {
        if (index > 2) throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    throw new Error("评分等待超时，请稍后在历史记录中查看。");
  }

  async function loadResult(homeworkId: number) {
    latestResult.value = await mobileApi.getResult(homeworkId);
  }

  function logout() {
    token.value = "";
    user.value = null;
    tasks.value = [];
    selectedTask.value = null;
    latestHomework.value = null;
    latestResult.value = null;
    history.value = [];
    progress.value = null;
    stage.value = "idle";
    uni.removeStorageSync(TOKEN_KEY);
    uni.reLaunch({ url: "/pages/login/index" });
  }

  return {
    username,
    password,
    token,
    user,
    tasks,
    selectedTask,
    latestHomework,
    latestResult,
    history,
    progress,
    stage,
    loading,
    message,
    todayTask,
    avgScore,
    resultImage,
    setMessage,
    login,
    restoreSession,
    refresh,
    openTask,
    loadTask,
    submitAndEvaluate,
    loadResult,
    logout,
    absoluteUrl
  };
});
