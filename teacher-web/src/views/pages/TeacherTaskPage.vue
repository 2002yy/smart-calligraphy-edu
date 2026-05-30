<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useTeacherStore } from "../../stores/teacher";
import type { TaskForm } from "../../types";
import TaskPanel from "../task/index.vue";

const store = useTeacherStore();
const { loading, courses, classes, tasks, taskForm, taskSubmitting } = storeToRefs(store);

function updateTaskForm(value: TaskForm) {
  taskForm.value = value;
}
</script>

<template>
  <TaskPanel
    :loading="loading"
    :courses="courses"
    :classes="classes"
    :tasks="tasks"
    :form="taskForm"
    :submitting="taskSubmitting"
    @update:form="updateTaskForm"
    @submit="store.createTask"
  />
</template>
