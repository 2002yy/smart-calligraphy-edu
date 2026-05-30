<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useTeacherStore } from "../../stores/teacher";
import DashboardPanel from "../dashboard/index.vue";

const store = useTeacherStore();
const { dashboard, classReport, activeClassName, dashboardLoading } = storeToRefs(store);
</script>

<template>
  <DashboardPanel
    :dashboard="dashboard"
    :report="classReport"
    :active-class-name="activeClassName"
    :loading="dashboardLoading"
  />
</template>
