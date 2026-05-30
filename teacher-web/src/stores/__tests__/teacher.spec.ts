import { setActivePinia, createPinia } from "pinia";
import { describe, it, expect, beforeEach, vi } from "vitest";

import { useTeacherStore } from "../teacher";

// ----- helpers -----

function mockResolved<T>(data: T) {
  return vi.fn().mockResolvedValue(data);
}

function mockRejected(message: string) {
  return vi.fn().mockRejectedValue(new Error(message));
}

// ----- mocks -----

const mockCurrentUser = {
  id: 1,
  username: "teacher01",
  name: "刘老师",
  role: "teacher",
  school_name: "四川大学",
  avatar_url: null,
};

const mockCourses = [
  { id: 10, name: "书法课", term: "2026春", teacher_id: 1, description: "", status: "active", created_at: null },
];

const mockClasses = [
  { id: 20, course_id: 10, name: "一班", invite_code: "AAA", student_count: 1 },
];

const mockTasks = [
  { id: 30, course_id: 10, class_id: 20, title: "基本笔画", description: "", practice_chars: ["永"], structure_weight: 40, center_weight: 30, stroke_order_weight: 30, created_by: 1, created_at: null, deadline: null },
];

const mockReviews = [
  { id: 40, homework_id: 1, teacher_id: 1, status: "reviewed", final_score: 88, score: 88, tags: ["good"], student_name: "张三" },
];

const mockDashboard = {
  class_id: 20, class_name: "一班", student_count: 1, task_count: 1,
  homework_count: 1, evaluated_count: 1, avg_score: 88, submit_rate: 1.0, top_issues: [],
};

const mockReport = {
  class_id: 20, student_count: 1, task_count: 1, homework_count: 1, evaluated_count: 1, avg_score: 88,
};

vi.mock("../../api", () => ({
  teacherApi: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    getCourses: vi.fn(),
    getClasses: vi.fn(),
    getTasks: vi.fn(),
    getReviews: vi.fn(),
    getDashboard: vi.fn(),
    getClassReport: vi.fn(),
    createCourse: vi.fn(),
    createClass: vi.fn(),
    createTask: vi.fn(),
  },
}));

import { teacherApi } from "../../api";

const api = teacherApi as unknown as Record<string, ReturnType<typeof vi.fn>>;

// ----- tests -----

describe("useTeacherStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    Object.values(api).forEach((m) => m.mockReset());
  });

  describe("login", () => {
    it("sets user and token on success, loads courses", async () => {
      api.login.mockResolvedValue({ access_token: "tok", token_type: "bearer", expires_in: 86400, user: mockCurrentUser });
      api.getCourses.mockResolvedValue(mockCourses);
      api.getClasses.mockResolvedValue(mockClasses);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getReviews.mockResolvedValue(mockReviews);
      api.getDashboard.mockResolvedValue(mockDashboard);
      api.getClassReport.mockResolvedValue(mockReport);

      const store = useTeacherStore();
      await store.login();

      expect(store.user).toEqual(mockCurrentUser);
      expect(store.token).toBe("tok");
      expect(localStorage.getItem("teacher_token")).toBe("tok");
      expect(store.courses).toEqual(mockCourses);
      expect(store.classes).toEqual(mockClasses);
      expect(store.tasks).toEqual(mockTasks);
      expect(store.reviews).toEqual(mockReviews);
      expect(store.dashboard).toEqual(mockDashboard);
      expect(store.classReport).toEqual(mockReport);
      expect(store.loading).toBe(false);
      expect(store.noticeType).toBe("success");
    });

    it("sets error and clears loading when login fails", async () => {
      api.login.mockRejectedValue(new Error("Connection refused"));

      const store = useTeacherStore();
      await store.login();

      expect(store.user).toBeNull();
      expect(store.loading).toBe(false);
      expect(store.noticeType).toBe("error");
    });
  });

  describe("restoreSession", () => {
    it("skips when token is empty", async () => {
      const store = useTeacherStore();
      await store.restoreSession();
      expect(api.getCurrentUser).not.toHaveBeenCalled();
    });

    it("restores user when token exists", async () => {
      localStorage.setItem("teacher_token", "tok");
      api.getCurrentUser.mockResolvedValue(mockCurrentUser);
      api.getCourses.mockResolvedValue(mockCourses);
      api.getClasses.mockResolvedValue(mockClasses);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getReviews.mockResolvedValue(mockReviews);
      api.getDashboard.mockResolvedValue(mockDashboard);
      api.getClassReport.mockResolvedValue(mockReport);

      const store = useTeacherStore();
      store.token = "tok";
      await store.restoreSession();

      expect(store.user).toEqual(mockCurrentUser);
    });
  });

  describe("changeCourse", () => {
    it("loads classes and selects first one", async () => {
      api.getClasses.mockResolvedValue(mockClasses);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getReviews.mockResolvedValue(mockReviews);
      api.getDashboard.mockResolvedValue(mockDashboard);
      api.getClassReport.mockResolvedValue(mockReport);

      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.courses = mockCourses;
      await store.changeCourse(10);

      expect(store.selectedCourseId).toBe(10);
      expect(store.classes).toEqual(mockClasses);
      expect(store.selectedClassId).toBe(20);
      expect(store.noticeType).toBe("success");
    });

    it("clears classes when courseId is null", async () => {
      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.classes = mockClasses;
      await store.changeCourse(null);

      expect(store.classes).toEqual([]);
      expect(store.selectedClassId).toBeNull();
    });
  });

  describe("changeClass", () => {
    it("loads class-linked data and sets notice", async () => {
      api.getTasks.mockResolvedValue(mockTasks);
      api.getReviews.mockResolvedValue(mockReviews);
      api.getDashboard.mockResolvedValue(mockDashboard);
      api.getClassReport.mockResolvedValue(mockReport);

      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.classes = mockClasses;
      await store.changeClass(20);

      expect(store.selectedClassId).toBe(20);
      expect(store.tasks).toEqual(mockTasks);
      expect(store.reviews).toEqual(mockReviews);
    });

    it("clears linked data when classId is null", async () => {
      const store = useTeacherStore();
      store.tasks = mockTasks;
      await store.changeClass(null);

      expect(store.tasks).toEqual([]);
      expect(store.reviews).toEqual([]);
    });
  });

  describe("createCourse", () => {
    it("rejects when name is missing", async () => {
      const store = useTeacherStore();
      await store.createCourse();
      expect(api.createCourse).not.toHaveBeenCalled();
      expect(store.noticeType).toBe("error");
    });

    it("creates and reloads courses", async () => {
      api.createCourse.mockResolvedValue({ id: 11, name: "新课", term: "2026秋", description: "", teacher_id: 1 });
      api.getCourses.mockResolvedValue([...mockCourses, { id: 11, name: "新课", term: "2026秋", description: "", teacher_id: 1 }]);
      api.getReviews.mockResolvedValue(mockReviews);

      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.courses = mockCourses;
      store.courseForm.name = "新课";
      store.courseForm.term = "2026秋";

      await store.createCourse();

      expect(store.courses.length).toBe(2);
      expect(store.selectedCourseId).toBe(11);
    });
  });

  describe("createClass", () => {
    it("rejects when no course selected", async () => {
      const store = useTeacherStore();
      await store.createClass();
      expect(api.createClass).not.toHaveBeenCalled();
      expect(store.noticeType).toBe("error");
    });

    it("rejects when class name is empty", async () => {
      const store = useTeacherStore();
      store.selectedCourseId = 10;
      await store.createClass();
      expect(api.createClass).not.toHaveBeenCalled();
    });
  });

  describe("createTask", () => {
    it("rejects when form fields are empty", async () => {
      const store = useTeacherStore();
      await store.createTask();
      expect(api.createTask).not.toHaveBeenCalled();
      expect(store.noticeType).toBe("error");
    });

    it("creates task and refreshes", async () => {
      api.createTask.mockResolvedValue(mockTasks[0]);
      api.getTasks.mockResolvedValue(mockTasks);
      api.getReviews.mockResolvedValue(mockReviews);
      api.getDashboard.mockResolvedValue(mockDashboard);
      api.getClassReport.mockResolvedValue(mockReport);

      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.taskForm.course_id = 10;
      store.taskForm.class_id = 20;
      store.taskForm.title = "基本笔画";

      await store.createTask();

      expect(api.createTask).toHaveBeenCalled();
      expect(store.noticeType).toBe("success");
    });
  });

  describe("logout", () => {
    it("clears all state and removes token", () => {
      localStorage.setItem("teacher_token", "tok");

      const store = useTeacherStore();
      store.user = mockCurrentUser;
      store.token = "tok";
      store.courses = mockCourses;

      store.logout();

      expect(store.user).toBeNull();
      expect(store.token).toBe("");
      expect(store.courses).toEqual([]);
      expect(localStorage.getItem("teacher_token")).toBeNull();
    });
  });
});
