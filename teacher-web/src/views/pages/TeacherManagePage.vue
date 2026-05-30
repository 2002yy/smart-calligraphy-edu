<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useTeacherStore } from "../../stores/teacher";
import type { ClassForm, CourseForm } from "../../types";
import ManagePanel from "../manage/index.vue";

const store = useTeacherStore();
const {
  loading,
  courseForm,
  classForm,
  courses,
  selectedCourseId,
  courseSubmitting,
  classSubmitting
} = storeToRefs(store);

function updateCourseForm(value: CourseForm) {
  courseForm.value = value;
}

function updateClassForm(value: ClassForm) {
  classForm.value = value;
}
</script>

<template>
  <ManagePanel
    :loading="loading"
    :course-form="courseForm"
    :class-form="classForm"
    :courses="courses"
    :selected-course-id="selectedCourseId"
    :creating-course="courseSubmitting"
    :creating-class="classSubmitting"
    @update:course-form="updateCourseForm"
    @update:class-form="updateClassForm"
    @update:selected-course-id="store.changeCourse"
    @create-course="store.createCourse"
    @create-class="store.createClass"
  />
</template>
