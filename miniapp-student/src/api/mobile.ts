import { request, upload } from "./request";
import type { ClassJoinResult, CurrentUser, EvaluationStart, Growth, Homework, LoginResponse, MobileResult, StudentTask } from "../types";

export const mobileApi = {
  login(username: string, password: string) {
    return request<LoginResponse>({
      url: "/api/mobile/login",
      method: "POST",
      data: { username, password }
    });
  },
  getCurrentUser() {
    return request<CurrentUser>({ url: "/api/mobile/me" });
  },
  joinClass(inviteCode: string) {
    return request<ClassJoinResult>({
      url: "/api/mobile/classes/join",
      method: "POST",
      data: { invite_code: inviteCode }
    });
  },
  getTasks() {
    return request<StudentTask[]>({ url: "/api/mobile/tasks" });
  },
  getTask(taskId: number) {
    return request<StudentTask>({ url: `/api/mobile/tasks/${taskId}` });
  },
  submitHomework(taskId: number, filePath: string) {
    return upload<Homework>({
      url: "/api/mobile/submissions",
      filePath,
      formData: { task_id: taskId }
    });
  },
  startEvaluation(homeworkId: number, provider: "auto" | "mock" | "qwen" = "auto") {
    return request<EvaluationStart>({
      url: `/api/mobile/submissions/${homeworkId}/evaluate?provider=${provider}`,
      method: "POST"
    });
  },
  getResult(homeworkId: number) {
    return request<MobileResult>({ url: `/api/mobile/submissions/${homeworkId}/result` });
  },
  getHistory() {
    return request<Homework[]>({ url: "/api/mobile/submissions" });
  },
  getProgress() {
    return request<Growth>({ url: "/api/mobile/profile/progress" });
  }
};
