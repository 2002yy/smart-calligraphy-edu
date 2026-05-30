import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/overview"
    },
    {
      path: "/overview",
      component: () => import("../views/StudentOverviewPage.vue")
    },
    {
      path: "/tasks",
      component: () => import("../views/StudentTaskPage.vue")
    },
    {
      path: "/submit",
      component: () => import("../views/StudentSubmitPage.vue")
    },
    {
      path: "/growth",
      component: () => import("../views/StudentGrowthPage.vue")
    }
  ]
});

export default router;
