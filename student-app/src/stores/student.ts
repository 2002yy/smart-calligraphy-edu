import { defineStore } from "pinia";
import { computed, reactive, ref } from "vue";

import { studentApi } from "../api";
import type {
  Classroom,
  CurrentUser,
  Evaluation,
  Growth,
  Homework,
  StudentTask,
  TaskSubmitForm
} from "../types";

type NoticeType = "info" | "success" | "error";

function defaultSubmitForm(): TaskSubmitForm {
  return {
    imageUrl: "",
    selectedFileName: ""
  };
}

export const useStudentStore = defineStore("student", () => {
  const loginForm = reactive({
    username: "student01",
    password: "123456"
  });

  const user = ref<CurrentUser | null>(null);
  const token = ref<string>(window.localStorage.getItem("student_token") || "");
  const classes = ref<Classroom[]>([]);
  const tasks = ref<StudentTask[]>([]);
  const selectedClassId = ref<number | null>(null);
  const selectedTaskId = ref<number | null>(null);
  const growth = ref<Growth | null>(null);
  const latestHomework = ref<Homework | null>(null);
  const evaluation = ref<Evaluation | null>(null);
  const selectedFile = ref<File | null>(null);
  const previewUrl = ref("");

  const loading = ref(false);
  const joining = ref(false);
  const submitting = ref(false);
  const evaluating = ref(false);
  const message = ref("请先登录学生账号，再选择班级和任务开始练习。");
  const noticeType = ref<NoticeType>("info");

  const joinForm = reactive({
    inviteCode: "CALLI2026"
  });

  const submitForm = reactive<TaskSubmitForm>(defaultSubmitForm());

  const selectedTask = computed(() => tasks.value.find((item) => item.id === selectedTaskId.value) || null);
  const studentSummary = computed(() => [
    { label: "已加入班级", value: classes.value.length },
    { label: "当前任务数", value: tasks.value.length },
    { label: "平均得分", value: growth.value?.avg_score ?? 0 }
  ]);

  function setNotice(nextMessage: string, type: NoticeType = "info") {
    message.value = nextMessage;
    noticeType.value = type;
  }

  function clearNotice() {
    setNotice("当前没有新的学习通知。", "info");
  }

  async function login() {
    loading.value = true;
    try {
      const response = await studentApi.login(loginForm.username, loginForm.password);
      user.value = response.user;
      token.value = response.access_token;
      window.localStorage.setItem("student_token", response.access_token);
      setNotice(`欢迎回来，${response.user.name}。学生端已成功连接后端服务。`, "success");
      await bootstrapStudentData();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "学生登录失败，请检查账号和后端服务。", "error");
    } finally {
      loading.value = false;
    }
  }

  async function restoreSession() {
    if (!token.value || user.value) {
      return;
    }

    loading.value = true;
    try {
      user.value = await studentApi.getCurrentUser();
      setNotice(`已恢复 ${user.value.name} 的登录状态，正在同步班级与任务数据。`, "success");
      await bootstrapStudentData();
    } catch (error) {
      clearSession();
      setNotice(error instanceof Error ? `${error.message}，请重新登录。` : "登录状态恢复失败，请重新登录。", "error");
    } finally {
      loading.value = false;
    }
  }

  async function bootstrapStudentData() {
    if (!user.value) {
      return;
    }

    try {
      classes.value = await studentApi.getClasses();
      selectedClassId.value = classes.value[0]?.id ?? null;
      if (selectedClassId.value) {
        tasks.value = await studentApi.getTasks(selectedClassId.value);
        selectedTaskId.value = tasks.value[0]?.id ?? null;
      } else {
        tasks.value = [];
        selectedTaskId.value = null;
      }
      growth.value = await studentApi.getGrowth(user.value.id);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "学生端数据加载失败，请稍后重试。", "error");
    }
  }

  async function changeClass(classId: number | null) {
    selectedClassId.value = classId;
    latestHomework.value = null;
    evaluation.value = null;

    if (!classId) {
      tasks.value = [];
      selectedTaskId.value = null;
      setNotice("已取消班级选择。", "info");
      return;
    }

    try {
      tasks.value = await studentApi.getTasks(classId);
      selectedTaskId.value = tasks.value[0]?.id ?? null;
      setNotice("班级已切换，任务列表已同步刷新。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "班级切换失败。", "error");
    }
  }

  function selectTask(taskId: number) {
    selectedTaskId.value = taskId;
    setNotice("已切换任务详情，可以继续查看说明或直接提交作业。", "info");
  }

  async function joinClass() {
    if (!selectedClassId.value || !user.value) {
      setNotice("请先选择班级，再输入邀请码加入。", "error");
      return;
    }

    joining.value = true;
    try {
      await studentApi.joinClass(selectedClassId.value, {
        invite_code: joinForm.inviteCode,
        student_id: user.value.id
      });
      classes.value = await studentApi.getClasses();
      setNotice("加入班级成功，可以开始查看任务并提交作业。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "加入班级失败。", "error");
    } finally {
      joining.value = false;
    }
  }

  async function submitHomework() {
    if (!selectedTask.value || !user.value) {
      setNotice("请先选择任务，再提交作业。", "error");
      return null;
    }

    if (!selectedFile.value) {
      setNotice("请先选择一张书法作业图片，再提交。", "error");
      return null;
    }

    submitting.value = true;
    try {
      const uploadResult = await studentApi.uploadHomework({
        task_id: selectedTask.value.id,
        file: selectedFile.value
      });

      latestHomework.value = await studentApi.submitHomework({
        homework_id: uploadResult.homework_id,
        task_id: selectedTask.value.id,
        student_id: user.value.id,
        image_url: uploadResult.file_url
      });
      submitForm.imageUrl = uploadResult.file_url;
      evaluation.value = null;
      growth.value = await studentApi.getGrowth(user.value.id);
      setNotice("作业提交成功，可以继续发起 AI 评测。", "success");
      return latestHomework.value;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "作业提交失败。", "error");
      return null;
    } finally {
      submitting.value = false;
    }
  }

  async function evaluateHomework(provider: "auto" | "mock" | "openai" | "qwen" = "auto") {
    if (!latestHomework.value || !user.value) {
      setNotice("请先提交作业，再发起评测。", "error");
      return;
    }

    evaluating.value = true;
    if (provider === "openai") {
      setNotice("正在调用 OpenAI 生成评分结果，请稍候（此为旧版评测，建议使用 Qwen）。", "info");
    } else if (provider === "qwen") {
      setNotice("正在通过阿里云百炼 Qwen3.5-omni-plus 评测书法作品，请稍候。", "info");
    } else {
      setNotice("正在生成 AI 评测结果，请稍候。", "info");
    }
    try {
      await studentApi.startEvaluation(latestHomework.value.id, provider, true);
      evaluation.value = await studentApi.getEvaluation(latestHomework.value.id);
      growth.value = await studentApi.getGrowth(user.value.id);
      if (provider === "openai") {
        setNotice("OpenAI 评分完成，结果卡片已更新。（旧版）", "success");
      } else if (provider === "qwen") {
        setNotice("Qwen 评测完成，结果卡片已更新。", "success");
      } else {
        setNotice("AI 评测完成，结果卡片已更新。", "success");
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");
    } finally {
      evaluating.value = false;
    }
  }

  async function waitEvaluationFinished(homeworkId: number, maxRetries = 40): Promise<Evaluation> {
    for (let i = 0; i < maxRetries; i++) {
      const result = await studentApi.getEvaluation(homeworkId);
      if (result.status === "finished") return result;
      if (result.status === "failed") throw new Error("AI 评测失败，请稍后重试");
      await new Promise((r) => setTimeout(r, 1500));
    }
    throw new Error("评测超时，请稍后刷新查看结果");
  }

  async function submitAndEvaluate() {
    if (submitting.value || evaluating.value) return;
    evaluating.value = true;
    try {
      const homework = await submitHomework();
      if (!homework) return;

      let provider: "qwen" | "auto" = "qwen";
      try {
        await studentApi.startEvaluation(homework.id, "qwen", true);
      } catch {
        provider = "auto";
        await studentApi.startEvaluation(homework.id, "auto", true);
      }

      evaluation.value = await waitEvaluationFinished(homework.id);
      growth.value = await studentApi.getGrowth(user.value!.id);
      setNotice(provider === "qwen" ? "AI 评分已完成" : "AI 评测完成，结果卡片已更新。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "AI 评测失败。", "error");
    } finally {
      evaluating.value = false;
    }
  }

  async function submitAndEvaluateWithOpenAI() {
    // DEPRECATED: 仅在调试时使用，默认隐藏
    if (submitting.value || evaluating.value) return;
    evaluating.value = true;
    try {
      const homework = await submitHomework();
      if (!homework) return;
      await evaluateHomework("openai");
    } finally {
      evaluating.value = false;
    }
  }

  function updateSelectedFile(file: File | null) {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value);
      previewUrl.value = "";
    }

    selectedFile.value = file;
    submitForm.selectedFileName = file?.name || "";
    if (!file) {
      submitForm.imageUrl = "";
      return;
    }
    previewUrl.value = URL.createObjectURL(file);
    setNotice(`已选择文件：${file.name}，现在可以提交作业或直接触发 Qwen AI 评分。`, "info");
  }

  function clearSession() {
    user.value = null;
    token.value = "";
    classes.value = [];
    tasks.value = [];
    selectedClassId.value = null;
    selectedTaskId.value = null;
    growth.value = null;
    latestHomework.value = null;
    evaluation.value = null;
    selectedFile.value = null;
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value);
      previewUrl.value = "";
    }
    joinForm.inviteCode = "CALLI2026";
    submitForm.imageUrl = defaultSubmitForm().imageUrl;
    submitForm.selectedFileName = defaultSubmitForm().selectedFileName;
    window.localStorage.removeItem("student_token");
  }

  function logout() {
    clearSession();
    setNotice("已退出登录，学生端状态已清空。", "info");
  }

  return {
    loginForm,
    user,
    token,
    classes,
    tasks,
    selectedClassId,
    selectedTaskId,
    growth,
    latestHomework,
    evaluation,
    selectedFile,
    previewUrl,
    loading,
    joining,
    submitting,
    evaluating,
    message,
    noticeType,
    joinForm,
    submitForm,
    selectedTask,
    studentSummary,
    setNotice,
    clearNotice,
    login,
    restoreSession,
    bootstrapStudentData,
    changeClass,
    selectTask,
    joinClass,
    submitHomework,
    evaluateHomework,
    submitAndEvaluate,
    submitAndEvaluateWithOpenAI,
    updateSelectedFile,
    logout
  };
});
