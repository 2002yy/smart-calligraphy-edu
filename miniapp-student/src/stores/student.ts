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
  const joining = ref(false);
  const inviteCode = ref("CALLI2026");
  const message = ref("Test build: login with student01 / 123456. Invite code: CALLI2026.");

  const todayTask = computed(() => tasks.value[0] || null);
  const avgScore = computed(() => Math.round((progress.value?.avg_score || 0) * 10));
  const resultImage = computed(() => absoluteUrl(latestResult.value?.image_url || latestHomework.value?.image_url));

  function setMessage(next: string) {
    message.value = next;
  }

  function fillDemoAccount() {
    username.value = "student01";
    password.value = "123456";
    inviteCode.value = "CALLI2026";
    setMessage("Demo info filled. Tap Login to continue.");
  }

  async function syncDataAfterLogin() {
    try {
      await refresh();
    } catch (syncError) {
      setMessage(
        syncError instanceof Error
          ? `Login success, but data sync failed: ${syncError.message}`
          : "Login success, but data sync failed. Check backend and try refresh."
      );
    }
  }

  async function login() {
    loading.value = true;
    try {
      const response = await mobileApi.login(username.value, password.value);
      token.value = response.access_token;
      user.value = response.user;
      uni.setStorageSync(TOKEN_KEY, response.access_token);
      setMessage("Login success. If no tasks appear, join with invite code CALLI2026.");
      uni.showToast({ title: "Login success", icon: "success" });
      await syncDataAfterLogin();
      uni.switchTab({ url: "/pages/home/index" });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed. Check account, password, and backend service.");
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
      await syncDataAfterLogin();
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
    setMessage(taskData.length ? "Tasks synced. You can start practice now." : "No tasks yet. Test invite code: CALLI2026.");
  }

  async function joinClass() {
    const code = inviteCode.value.trim();
    if (!code) {
      setMessage("Enter the invite code. Test build code: CALLI2026.");
      return;
    }

    joining.value = true;
    try {
      const result = await mobileApi.joinClass(code);
      await refresh();
      uni.showToast({ title: "Joined", icon: "success" });
      setMessage(`Joined ${result.class_name}. Task list refreshed.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Join failed. Check invite code CALLI2026 and backend data.");
    } finally {
      joining.value = false;
    }
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
      setMessage("Select a task first. If none exists, join with CALLI2026.");
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
      setMessage(error instanceof Error ? error.message : "Upload or evaluation failed. Please try again.");
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
    throw new Error("Evaluation timed out. Check history later.");
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
    joining,
    inviteCode,
    message,
    todayTask,
    avgScore,
    resultImage,
    setMessage,
    fillDemoAccount,
    login,
    restoreSession,
    refresh,
    joinClass,
    openTask,
    loadTask,
    submitAndEvaluate,
    loadResult,
    logout,
    absoluteUrl
  };
});
