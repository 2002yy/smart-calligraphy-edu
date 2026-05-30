import request from "./lib/request";
import type {
  ClassReport,
  Classroom,
  Course,
  DashboardData,
  LoginResponse,
  Review,
  Task
} from "./types";

export const teacherApi = {
  login(username: string, password: string) {
    return request.post<never, LoginResponse>("/api/v1/auth/login", { username, password });
  },
  getCurrentUser() {
    return request.get<never, LoginResponse["user"]>("/api/v1/auth/me");
  },
  getCourses(teacherId?: number) {
    return request.get<never, Course[]>("/api/v1/courses", { params: teacherId ? { teacher_id: teacherId } : undefined });
  },
  createCourse(payload: {
    name: string;
    term: string;
    description: string;
    teacher_id: number;
  }) {
    return request.post<never, Course>("/api/v1/courses", payload);
  },
  getClasses(courseId?: number) {
    return request.get<never, Classroom[]>("/api/v1/classes", { params: courseId ? { course_id: courseId } : undefined });
  },
  createClass(payload: {
    course_id: number;
    name: string;
    invite_code: string | null;
  }) {
    return request.post<never, Classroom>("/api/v1/classes", payload);
  },
  getTasks(classId?: number) {
    return request.get<never, Task[]>("/api/v1/tasks", { params: classId ? { class_id: classId } : undefined });
  },
  createTask(payload: {
    course_id: number;
    class_id: number;
    title: string;
    description: string;
    practice_chars: string[];
    structure_weight: number;
    center_weight: number;
    stroke_order_weight: number;
    deadline: string | null;
    created_by: number;
  }) {
    return request.post<never, Task>("/api/v1/tasks", payload);
  },
  getReviews(teacherId?: number) {
    return request.get<never, Review[]>("/api/v1/reviews", { params: teacherId ? { teacher_id: teacherId } : undefined });
  },
  getDashboard(classId: number) {
    return request.get<never, DashboardData>(`/api/v1/dashboard/class/${classId}`);
  },
  getClassReport(classId: number) {
    return request.get<never, ClassReport>(`/api/v1/reports/class/${classId}`);
  }
};
