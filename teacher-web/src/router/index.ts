import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/dashboard"
    },
    {
      path: "/dashboard",
      component: () => import("../views/pages/TeacherDashboardPage.vue")
    },
    {
      path: "/manage",
      component: () => import("../views/pages/TeacherManagePage.vue")
    },
    {
      path: "/tasks",
      component: () => import("../views/pages/TeacherTaskPage.vue")
    },
    {
      path: "/reviews",
      component: () => import("../views/pages/TeacherReviewPage.vue")
    }
  ]
});

export default router;
