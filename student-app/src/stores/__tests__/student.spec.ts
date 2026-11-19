import { setActivePinia, createPinia } from "pinia";
import { describe, it, expect, beforeEach, vi } from "vitest";

import { useStudentStore } from "../student";

// ----- mocks -----

const mockCurrentUser = {
  id: 2,
  username: "student01",
  name: "张三",
  role: "student",
  school_name: "四川大学",
  avatar_url: null,
};

const mockClasses = [
  { id: 20, course_id: 10, name: "一班", invite_code: "CALLI2026", student_count: 1 },
];

const mockTasks = [
  { id: 30, course_id: 10, class_id: 20, title: "基本笔画", description: "", practice_chars: ["永"], structure_weight: 40, center_weight: 30, stroke_order_weight: 30, deadline: null },
];

const mockGrowth = { user_id: 2, avg_score: 88 };

const mockUploadResult = { homework_id: 100, file_url: "/uploads/test.png", status: "submitted" };

const mockHomework = { id: 100, task_id: 30, student_id: 2, status: "submitted", image_url: "/uploads/test.png", submitted_at: null, processed_image_url: null };

const mockEvaluation = {
  id: 1, homework_id: 100, score: 88, total_score: 88,
  structure_score: 90, center_score: 85, stroke_order_score: 85,
  tags: ["good"], issues: ["good"], advice: "Keep it up",
  compare_image_url: null, status: "finished", created_at: null,
};

vi.mock("../../api", () => ({
  studentApi: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    getClasses: vi.fn(),
    joinClass: vi.fn(),
    getTasks: vi.fn(),
    uploadHomework: vi.fn(),
    submitHomework: vi.fn(),
    startEvaluation: vi.fn(),
    getEvaluation: vi.fn(),
    getGrowth: vi.fn(),
    getTagTrend: vi.fn(),
  },
}));

import { studentApi } from "../../api";

const api = studentApi as unknown as Record<string, ReturnType<typeof vi.fn>>;

// ----- tests -----

describe("useStudentStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    Object.values(api).forEach((m) => m.mockReset());
  });

  describe("login", () => {
    it("sets user and token on success, loads classes and growth", async () => {
      api.login.mockResolvedValue({ access_token: "tok", token_type: "bearer", expires_in: 86400, user: mockCurrentUser });
      api.getClasses.mockResolvedValue(mockClasses);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getGrowth.mockResolvedValue(mockGrowth);

      const store = useStudentStore();
      await store.login();

      expect(store.user).toEqual(mockCurrentUser);
      expect(store.token).toBe("tok");
      expect(localStorage.getItem("student_token")).toBe("tok");
      expect(store.classes).toEqual(mockClasses);
      expect(store.tasks).toEqual(mockTasks);
      expect(store.growth).toEqual(mockGrowth);
    });

    it("sets error when login fails", async () => {
      api.login.mockRejectedValue(new Error("Connection refused"));

      const store = useStudentStore();
      await store.login();

      expect(store.user).toBeNull();
      expect(store.noticeType).toBe("error");
    });
  });

  describe("restoreSession", () => {
    it("skips when token is empty", async () => {
      const store = useStudentStore();
      await store.restoreSession();
      expect(api.getCurrentUser).not.toHaveBeenCalled();
    });

    it("restores user when token exists", async () => {
      localStorage.setItem("student_token", "tok");
      api.getCurrentUser.mockResolvedValue(mockCurrentUser);
      api.getClasses.mockResolvedValue(mockClasses);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getGrowth.mockResolvedValue(mockGrowth);

      const store = useStudentStore();
      store.token = "tok";
      await store.restoreSession();

      expect(store.user).toEqual(mockCurrentUser);
    });
  });

  describe("changeClass", () => {
    it("loads tasks for the selected class", async () => {
      api.getTasks.mockResolvedValue(mockTasks);

      const store = useStudentStore();
      await store.changeClass(20);

      expect(store.selectedClassId).toBe(20);
      expect(store.tasks).toEqual(mockTasks);
    });

    it("clears tasks when classId is null", async () => {
      const store = useStudentStore();
      store.tasks = mockTasks;
      await store.changeClass(null);

      expect(store.tasks).toEqual([]);
      expect(store.evaluation).toBeNull();
    });
  });

  describe("selectTask", () => {
    it("updates selectedTaskId and shows info notice", () => {
      const store = useStudentStore();
      store.selectTask(30);
      expect(store.selectedTaskId).toBe(30);
      expect(store.noticeType).toBe("info");
    });
  });

  describe("joinClass", () => {
    it("rejects when no class is selected", async () => {
      const store = useStudentStore();
      store.user = mockCurrentUser;
      await store.joinClass();
      expect(api.joinClass).not.toHaveBeenCalled();
      expect(store.noticeType).toBe("error");
    });
  });

  describe("submitHomework", () => {
    it("rejects when no task is selected", async () => {
      const store = useStudentStore();
      await store.submitHomework();
      expect(api.uploadHomework).not.toHaveBeenCalled();
    });

    it("rejects when no file is selected", async () => {
      const store = useStudentStore();
      store.tasks = mockTasks;
      store.selectedTaskId = 30;
      await store.submitHomework();
      expect(api.uploadHomework).not.toHaveBeenCalled();
    });

    it("uploads, submits, and refreshes growth", async () => {
      api.uploadHomework.mockResolvedValue(mockUploadResult);
      api.submitHomework.mockResolvedValue(mockHomework);
      api.getGrowth.mockResolvedValue(mockGrowth);

      const store = useStudentStore();
      store.user = mockCurrentUser;
      store.tasks = mockTasks;
      store.selectedTaskId = 30;
      store.selectedFile = new File(["fake"], "test.png", { type: "image/png" });

      const result = await store.submitHomework();

      expect(result).toEqual(mockHomework);
      expect(store.latestHomework).toEqual(mockHomework);
      expect(store.growth).toEqual(mockGrowth);
      expect(store.noticeType).toBe("success");
    });
  });

  describe("evaluateHomework", () => {
    it("starts evaluation and fetches result", async () => {
      api.startEvaluation.mockResolvedValue({ status: "finished", homework_id: 100, evaluation_id: 1, provider: "mock" });
      api.getEvaluation.mockResolvedValue(mockEvaluation);
      api.getGrowth.mockResolvedValue(mockGrowth);

      const store = useStudentStore();
      store.user = mockCurrentUser;
      store.latestHomework = mockHomework;
      await store.evaluateHomework("mock");

      expect(store.evaluation).toEqual(mockEvaluation);
      expect(store.evaluationProvider).toBe("mock");
      expect(store.noticeType).toBe("success");
    });
  });

  describe("submitAndEvaluate", () => {
    function readyToSubmit() {
      api.uploadHomework.mockResolvedValue(mockUploadResult);
      api.submitHomework.mockResolvedValue(mockHomework);
      api.getGrowth.mockResolvedValue(mockGrowth);
      api.getTagTrend.mockResolvedValue(null);

      const store = useStudentStore();
      store.user = mockCurrentUser;
      store.tasks = mockTasks;
      store.selectedTaskId = 30;
      store.selectedFile = new File(["fake"], "test.png", { type: "image/png" });
      return store;
    }

    it("keeps the uploaded homework but never silently falls back to mock when Qwen fails", async () => {
      const store = readyToSubmit();
      api.startEvaluation.mockRejectedValue(new Error("Qwen 评测未启用"));

      await store.submitAndEvaluate();

      expect(api.startEvaluation).toHaveBeenCalledExactlyOnceWith(100, "qwen", true);
      expect(store.latestHomework).toEqual(mockHomework);
      expect(store.evaluation).toBeNull();
      expect(store.submitStage).toBe("failed");
      expect(store.noticeType).toBe("error");
      expect(store.message).toContain("Qwen 评测未启用");
    });

    it("generates a clearly labeled mock score only when explicitly requested", async () => {
      const store = readyToSubmit();
      api.startEvaluation.mockResolvedValue({ status: "finished", homework_id: 100, evaluation_id: 1, provider: "mock" });
      api.getEvaluation.mockResolvedValue(mockEvaluation);

      await store.submitAndEvaluate("mock");

      expect(api.startEvaluation).toHaveBeenCalledExactlyOnceWith(100, "mock", true);
      expect(store.evaluationProvider).toBe("mock");
      expect(store.submitStage).toBe("finished");
      expect(store.message).toContain("非 AI 评分");
    });

    it("does not present a mock result as Qwen when the backend returns a different provider", async () => {
      const store = readyToSubmit();
      api.startEvaluation.mockResolvedValue({ status: "finished", homework_id: 100, evaluation_id: 1, provider: "mock" });

      await store.submitAndEvaluate();

      expect(api.startEvaluation).toHaveBeenCalledExactlyOnceWith(100, "qwen", true);
      expect(api.getEvaluation).not.toHaveBeenCalled();
      expect(store.submitStage).toBe("failed");
      expect(store.message).toContain("来源与请求不一致");
    });
  });

  describe("logout", () => {
    it("clears all state and removes token", () => {
      localStorage.setItem("student_token", "tok");

      const store = useStudentStore();
      store.user = mockCurrentUser;
      store.token = "tok";
      store.classes = mockClasses;
      store.tasks = mockTasks;

      store.logout();

      expect(store.user).toBeNull();
      expect(store.token).toBe("");
      expect(store.classes).toEqual([]);
      expect(store.tasks).toEqual([]);
      expect(localStorage.getItem("student_token")).toBeNull();
    });
  });

  describe("updateSelectedFile", () => {
    it("sets the file and updates preview", () => {
      const store = useStudentStore();
      store.latestHomework = mockHomework;
      store.evaluation = mockEvaluation;
      store.evaluationProvider = "mock";
      store.submitStage = "finished";
      const file = new File(["fake"], "test.png", { type: "image/png" });
      store.updateSelectedFile(file);

      expect(store.selectedFile).toStrictEqual(file);
      expect(store.submitForm.selectedFileName).toBe("test.png");
      expect(store.previewUrl).toBeTruthy();
      expect(store.latestHomework).toBeNull();
      expect(store.evaluation).toBeNull();
      expect(store.evaluationProvider).toBeNull();
      expect(store.submitStage).toBe("idle");
    });

    it("clears file when null is passed", () => {
      const store = useStudentStore();
      store.updateSelectedFile(null);

      expect(store.selectedFile).toBeNull();
      expect(store.submitForm.selectedFileName).toBe("");
      expect(store.submitForm.imageUrl).toBe("");
    });
  });
});
