import request from "./lib/request";
import type {
  Classroom,
  Evaluation,
  Growth,
  Homework,
  HomeworkUploadResult,
  LoginResponse,
  StudentTask
} from "./types";

export const studentApi = {
  login(username: string, password: string) {
    return request.post<never, LoginResponse>("/api/v1/auth/login", { username, password });
  },
  getCurrentUser() {
    return request.get<never, LoginResponse["user"]>("/api/v1/auth/me");
  },
  getClasses() {
    return request.get<never, Classroom[]>("/api/v1/classes");
  },
  joinClass(
    classId: number,
    payload: {
      invite_code: string;
      student_id: number;
    }
  ) {
    return request.post<never, { class_id: number; student_id: number; status: string }>(`/api/v1/classes/${classId}/join`, payload);
  },
  getTasks(classId: number) {
    return request.get<never, StudentTask[]>("/api/v1/tasks", { params: { class_id: classId } });
  },
  uploadHomework(payload: {
    task_id: number;
    student_id: number;
    file: File;
  }) {
    const formData = new FormData();
    formData.append("task_id", String(payload.task_id));
    formData.append("student_id", String(payload.student_id));
    formData.append("file", payload.file);
    return request.post<FormData, HomeworkUploadResult>("/api/v1/homework/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });
  },
  submitHomework(payload: {
    homework_id?: number;
    task_id: number;
    student_id: number;
    image_url?: string;
  }) {
    return request.post<never, Homework>("/api/v1/homework", payload);
  },
  startEvaluation(
    homeworkId: number,
    provider: "auto" | "mock" | "openai" | "qwen" = "auto",
    forceRefresh = false
  ) {
    return request.post<never, { status: string; homework_id: number; evaluation_id: number; provider: string }>(
      "/api/v1/evaluation/start",
      {
        homework_id: homeworkId,
        provider,
        force_refresh: forceRefresh
      }
    );
  },
  getEvaluation(homeworkId: number) {
    return request.get<never, Evaluation>(`/api/v1/evaluation/${homeworkId}`);
  },
  getGrowth(userId: number) {
    return request.get<never, Growth>(`/api/v1/users/${userId}/growth`);
  },
  getEvaluationProviders() {
    return request.get<never, Record<string, {enabled: boolean; configured?: boolean; deprecated?: boolean}>>("/api/v1/evaluation/providers");
  }
};
