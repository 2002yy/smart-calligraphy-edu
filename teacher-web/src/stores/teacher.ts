import { defineStore } from "pinia";
import { computed, reactive, ref } from "vue";

import { teacherApi } from "../api";
import type {
  ClassForm,
  ClassReport,
  Classroom,
  Course,
  CourseForm,
  CurrentUser,
  DashboardData,
  Review,
  Task,
  TaskForm
} from "../types";

type NoticeType = "info" | "success" | "error";

function defaultTaskForm(): TaskForm {
  return {
    course_id: null,
    class_id: null,
    title: "",
    description: "",
    practiceChars: "永、木、中、人",
    deadline: ""
  };
}

function defaultCourseForm(): CourseForm {
  return {
    name: "",
    term: "2026春季",
    description: ""
  };
}

function defaultClassForm(): ClassForm {
  return {
    name: "",
    inviteCode: ""
  };
}

export const useTeacherStore = defineStore("teacher", () => {
  const loginForm = reactive({
    username: "teacher01",
    password: "123456"
  });

  const user = ref<CurrentUser | null>(null);
  const token = ref<string>(window.localStorage.getItem("teacher_token") || "");
  const loading = ref(false);
  const dashboardLoading = ref(false);
  const reviewLoading = ref(false);
  const taskSubmitting = ref(false);
  const courseSubmitting = ref(false);
  const classSubmitting = ref(false);
  const message = ref("请先登录教师账号，再创建课程、班级并发布训练任务。");
  const noticeType = ref<NoticeType>("info");

  const courses = ref<Course[]>([]);
  const classes = ref<Classroom[]>([]);
  const tasks = ref<Task[]>([]);
  const reviews = ref<Review[]>([]);
  const dashboard = ref<DashboardData | null>(null);
  const classReport = ref<ClassReport | null>(null);

  const selectedCourseId = ref<number | null>(null);
  const selectedClassId = ref<number | null>(null);

  const taskForm = ref<TaskForm>(defaultTaskForm());
  const courseForm = ref<CourseForm>(defaultCourseForm());
  const classForm = ref<ClassForm>(defaultClassForm());

  const isAuthenticated = computed(() => Boolean(user.value && token.value));
  const selectedCourse = computed(() => courses.value.find((item) => item.id === selectedCourseId.value) || null);
  const selectedClass = computed(() => classes.value.find((item) => item.id === selectedClassId.value) || null);
  const activeClassName = computed(() => selectedClass.value?.name || "未选择班级");
  const teacherSummary = computed(() => [
    { label: "课程总数", value: courses.value.length },
    { label: "班级总数", value: classes.value.length },
    { label: "任务数量", value: tasks.value.length },
    { label: "批阅记录", value: reviews.value.length }
  ]);

  function setNotice(nextMessage: string, type: NoticeType = "info") {
    message.value = nextMessage;
    noticeType.value = type;
  }

  function clearNotice() {
    setNotice("当前没有新的系统通知。", "info");
  }

  async function login() {
    loading.value = true;
    try {
      const response = await teacherApi.login(loginForm.username, loginForm.password);
      user.value = response.user;
      token.value = response.access_token;
      window.localStorage.setItem("teacher_token", response.access_token);
      setNotice(`欢迎回来，${response.user.name}。教师端已成功连接后端服务。`, "success");
      await bootstrapTeacherData();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "教师登录失败，请检查账号和后端服务。", "error");
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
      user.value = await teacherApi.getCurrentUser();
      setNotice(`已恢复 ${user.value.name} 的登录状态，正在同步课程与班级数据。`, "success");
      await bootstrapTeacherData();
    } catch (error) {
      clearSession();
      setNotice(error instanceof Error ? `${error.message}，请重新登录。` : "登录状态恢复失败，请重新登录。", "error");
    } finally {
      loading.value = false;
    }
  }

  async function bootstrapTeacherData() {
    if (!user.value) {
      return;
    }

    try {
      courses.value = await teacherApi.getCourses(user.value.id);
      selectedCourseId.value = courses.value[0]?.id ?? null;

      if (selectedCourseId.value) {
        classes.value = await teacherApi.getClasses(selectedCourseId.value);
        selectedClassId.value = classes.value[0]?.id ?? null;
      } else {
        classes.value = [];
        selectedClassId.value = null;
      }

      taskForm.value = {
        ...taskForm.value,
        course_id: selectedCourseId.value,
        class_id: selectedClassId.value
      };

      await refreshClassLinkedData();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "教师端数据加载失败，请稍后重试。", "error");
    }
  }

  async function refreshClassLinkedData() {
    if (!selectedClassId.value || !user.value) {
      tasks.value = [];
      reviews.value = [];
      dashboard.value = null;
      classReport.value = null;
      return;
    }

    dashboardLoading.value = true;
    reviewLoading.value = true;
    try {
      const [taskResult, reviewResult, dashboardResult, reportResult] = await Promise.all([
        teacherApi.getTasks(selectedClassId.value),
        teacherApi.getReviews(user.value.id),
        teacherApi.getDashboard(selectedClassId.value),
        teacherApi.getClassReport(selectedClassId.value)
      ]);

      tasks.value = taskResult;
      reviews.value = reviewResult;
      dashboard.value = dashboardResult;
      classReport.value = reportResult;
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "班级关联数据刷新失败，请检查接口服务。", "error");
    } finally {
      dashboardLoading.value = false;
      reviewLoading.value = false;
    }
  }

  async function changeCourse(courseId: number | null) {
    selectedCourseId.value = courseId;
    taskForm.value = {
      ...taskForm.value,
      course_id: courseId,
      class_id: null
    };

    if (!courseId) {
      classes.value = [];
      selectedClassId.value = null;
      await refreshClassLinkedData();
      setNotice("已清空课程选择，请重新选择课程。", "info");
      return;
    }

    try {
      classes.value = await teacherApi.getClasses(courseId);
      selectedClassId.value = classes.value[0]?.id ?? null;
      taskForm.value = {
        ...taskForm.value,
        class_id: selectedClassId.value
      };
      await refreshClassLinkedData();
      setNotice(`已切换到课程《${selectedCourse.value?.name || "未命名课程"}》。`, "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "课程切换失败。", "error");
    }
  }

  async function changeClass(classId: number | null) {
    selectedClassId.value = classId;
    taskForm.value = {
      ...taskForm.value,
      class_id: classId
    };

    try {
      await refreshClassLinkedData();
      setNotice(
        classId ? `当前班级已切换为《${selectedClass.value?.name || "未命名班级"}》。` : "已取消班级选择。",
        classId ? "success" : "info"
      );
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "班级切换失败。", "error");
    }
  }

  async function createCourse() {
    if (!user.value || !courseForm.value.name || !courseForm.value.term) {
      setNotice("请先填写课程名称和开课学期。", "error");
      return;
    }

    courseSubmitting.value = true;
    try {
      const created = await teacherApi.createCourse({
        name: courseForm.value.name,
        term: courseForm.value.term,
        description: courseForm.value.description,
        teacher_id: user.value.id
      });

      courses.value = await teacherApi.getCourses(user.value.id);
      selectedCourseId.value = created.id;
      classes.value = [];
      selectedClassId.value = null;
      taskForm.value = {
        ...taskForm.value,
        course_id: created.id,
        class_id: null
      };
      courseForm.value = defaultCourseForm();
      dashboard.value = null;
      classReport.value = null;
      tasks.value = [];
      reviews.value = await teacherApi.getReviews(user.value.id);
      setNotice(`课程创建成功：《${created.name}》。`, "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "课程创建失败。", "error");
    } finally {
      courseSubmitting.value = false;
    }
  }

  async function createClass() {
    if (!selectedCourseId.value || !classForm.value.name) {
      setNotice("请先选择课程并填写班级名称。", "error");
      return;
    }

    classSubmitting.value = true;
    try {
      const created = await teacherApi.createClass({
        course_id: selectedCourseId.value,
        name: classForm.value.name,
        invite_code: classForm.value.inviteCode || null
      });

      classes.value = await teacherApi.getClasses(selectedCourseId.value);
      selectedClassId.value = created.id;
      classForm.value = defaultClassForm();
      taskForm.value = {
        ...taskForm.value,
        class_id: created.id
      };
      await refreshClassLinkedData();
      setNotice(`班级创建成功：《${created.name}》。`, "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "班级创建失败。", "error");
    } finally {
      classSubmitting.value = false;
    }
  }

  async function createTask() {
    if (!user.value || !taskForm.value.course_id || !taskForm.value.class_id || !taskForm.value.title) {
      setNotice("请选择课程和班级，并补充任务标题后再发布。", "error");
      return;
    }

    taskSubmitting.value = true;
    try {
      const practiceChars = taskForm.value.practiceChars
        .split(/[、,，\s]+/)
        .map((item) => item.trim())
        .filter(Boolean);

      await teacherApi.createTask({
        course_id: taskForm.value.course_id,
        class_id: taskForm.value.class_id,
        title: taskForm.value.title,
        description: taskForm.value.description,
        practice_chars: practiceChars,
        structure_weight: 40,
        center_weight: 30,
        stroke_order_weight: 30,
        deadline: taskForm.value.deadline ? new Date(taskForm.value.deadline).toISOString() : null,
        created_by: user.value.id
      });

      taskForm.value = {
        ...defaultTaskForm(),
        course_id: selectedCourseId.value,
        class_id: selectedClassId.value
      };
      await refreshClassLinkedData();
      setNotice("训练任务发布成功，任务列表和教学看板已同步刷新。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "任务发布失败。", "error");
    } finally {
      taskSubmitting.value = false;
    }
  }

  async function deleteTask(taskId: number) {
    try {
      await teacherApi.deleteTask(taskId);
      tasks.value = tasks.value.filter((item) => item.id !== taskId);
      setNotice("任务已删除。", "success");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "任务删除失败。", "error");
    }
  }

  function clearSession() {
    user.value = null;
    token.value = "";
    courses.value = [];
    classes.value = [];
    tasks.value = [];
    reviews.value = [];
    dashboard.value = null;
    classReport.value = null;
    selectedCourseId.value = null;
    selectedClassId.value = null;
    taskForm.value = defaultTaskForm();
    courseForm.value = defaultCourseForm();
    classForm.value = defaultClassForm();
    window.localStorage.removeItem("teacher_token");
  }

  function logout() {
    clearSession();
    setNotice("已退出登录，教师端状态已清空。", "info");
  }

  return {
    loginForm,
    user,
    token,
    loading,
    dashboardLoading,
    reviewLoading,
    taskSubmitting,
    courseSubmitting,
    classSubmitting,
    message,
    noticeType,
    courses,
    classes,
    tasks,
    reviews,
    dashboard,
    classReport,
    selectedCourseId,
    selectedClassId,
    taskForm,
    courseForm,
    classForm,
    isAuthenticated,
    selectedCourse,
    selectedClass,
    activeClassName,
    teacherSummary,
    setNotice,
    clearNotice,
    login,
    restoreSession,
    bootstrapTeacherData,
    refreshClassLinkedData,
    changeCourse,
    changeClass,
    createCourse,
    createClass,
    createTask,
    deleteTask,
    logout
  };
});
