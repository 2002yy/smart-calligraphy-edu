<script setup lang="ts">
import AppSkeleton from "../../components/AppSkeleton.vue";
import CollapsibleIntro from "../../components/CollapsibleIntro.vue";
import type { ClassForm, Course, CourseForm } from "../../types";

const props = defineProps<{
  loading?: boolean;
  courseForm: CourseForm;
  classForm: ClassForm;
  courses: Course[];
  selectedCourseId: number | null;
  creatingCourse: boolean;
  creatingClass: boolean;
}>();

const emit = defineEmits<{
  "update:course-form": [value: CourseForm];
  "update:class-form": [value: ClassForm];
  "update:selected-course-id": [value: number | null];
  createCourse: [];
  createClass: [];
}>();

function updateCourseField<K extends keyof CourseForm>(key: K, value: CourseForm[K]) {
  emit("update:course-form", { ...props.courseForm, [key]: value });
}

function updateClassField<K extends keyof ClassForm>(key: K, value: ClassForm[K]) {
  emit("update:class-form", { ...props.classForm, [key]: value });
}

function hasCourseNameError() {
  return !props.courseForm.name.trim();
}

function hasCourseTermError() {
  return !props.courseForm.term.trim();
}

function hasSelectedCourseError() {
  return props.courses.length > 0 && !props.selectedCourseId;
}

function hasClassNameError() {
  return !props.classForm.name.trim();
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">课程班级</p>
        <h2>先搭教学结构，再进入任务链路</h2>
      </div>
      <span class="badge">教师端起点</span>
    </div>

    <CollapsibleIntro storageKey="intro-manage">
      先创建课程，再创建班级，这样后续任务、作业、评测和报告都会有清晰的对应关系。
    </CollapsibleIntro>

    <div v-if="loading && !courses.length" class="form-grid">
      <section class="form-shell skeleton-shell">
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="4" />
      </section>
      <section class="form-shell skeleton-shell">
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="3" />
      </section>
    </div>

    <div v-else class="form-grid">
      <form class="form-shell" @submit.prevent="$emit('createCourse')">
        <div class="section-head">
          <h3>创建课程</h3>
          <span>第一步</span>
        </div>

        <p class="section-copy">
          建议用”教学主题 + 课程属性”的方式命名课程，例如”智慧书法素养提升课”，方便区分不同课程。
        </p>

        <label class="field-block">
          <span>课程名称</span>
          <input
            :value="courseForm.name"
            type="text"
            placeholder="例如：智慧书法素养提升课"
            @input="updateCourseField('name', ($event.target as HTMLInputElement).value)"
          />
          <small v-if="hasCourseNameError()" class="validation-error">课程名称不能为空。</small>
        </label>

        <label class="field-block">
          <span>开课学期</span>
          <input
            :value="courseForm.term"
            type="text"
            placeholder="例如：2026 春季"
            @input="updateCourseField('term', ($event.target as HTMLInputElement).value)"
          />
          <small v-if="hasCourseTermError()" class="validation-error">开课学期不能为空。</small>
        </label>

        <label class="field-block">
          <span>课程说明</span>
          <textarea
            :value="courseForm.description"
            rows="5"
            placeholder="简要说明教学目标、训练重点和适用对象"
            @input="updateCourseField('description', ($event.target as HTMLTextAreaElement).value)"
          />
        </label>

        <button class="primary-btn action-btn" :disabled="creatingCourse">
          <span class="btn-content">
            <span v-if="creatingCourse" class="btn-spinner"></span>
            {{ creatingCourse ? "创建中..." : "创建课程" }}
          </span>
        </button>
      </form>

      <form class="form-shell" @submit.prevent="$emit('createClass')">
        <div class="section-head">
          <h3>创建班级</h3>
          <span>第二步</span>
        </div>

        <p class="section-copy">
          班级是学生加入与任务发布的直接对象。建议名称中带上学期信息，例如”2026春季班”。
        </p>

        <label class="field-block">
          <span>绑定课程</span>
          <select
            :value="selectedCourseId ?? ''"
            @change="$emit('update:selected-course-id', Number(($event.target as HTMLSelectElement).value) || null)"
          >
            <option value="">请选择课程</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
          <small v-if="hasSelectedCourseError()" class="validation-error">创建班级前请先选择课程。</small>
        </label>

        <label class="field-block">
          <span>班级名称</span>
          <input
            :value="classForm.name"
            type="text"
            placeholder="例如：2026 春季实验班"
            @input="updateClassField('name', ($event.target as HTMLInputElement).value)"
          />
          <small v-if="hasClassNameError()" class="validation-error">班级名称不能为空。</small>
        </label>

        <label class="field-block">
          <span>邀请码</span>
          <input
            :value="classForm.inviteCode"
            type="text"
            placeholder="可选，留空则由系统生成"
            @input="updateClassField('inviteCode', ($event.target as HTMLInputElement).value)"
          />
        </label>

        <button class="primary-btn action-btn" :disabled="creatingClass">
          <span class="btn-content">
            <span v-if="creatingClass" class="btn-spinner"></span>
            {{ creatingClass ? "创建中..." : "创建班级" }}
          </span>
        </button>
      </form>
    </div>

    <section class="after-block">
      <strong>下一步建议</strong>
      <p>课程和班级建好后，可以进入”任务编排”发布训练任务，再回到”教学看板”查看学生的学习反馈。</p>
    </section>
  </section>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 26px;
}

.form-shell {
  display: grid;
  gap: 14px;
  align-content: start;
}

.skeleton-shell {
  min-height: 380px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.section-head h3 {
  margin: 0;
  font-size: 24px;
}

.section-head span {
  color: var(--accent-deep);
  font-size: 13px;
}

.section-copy {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.field-block {
  display: grid;
  gap: 8px;
}

.field-block span {
  color: var(--muted);
  font-size: 13px;
}

.validation-error {
  color: #b5442b;
  font-size: 12px;
  line-height: 1.6;
}

textarea {
  resize: vertical;
  min-height: 122px;
}

.action-btn {
  margin-top: 4px;
}

.btn-content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  animation: spin 0.8s linear infinite;
}

@media (max-width: 1280px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
