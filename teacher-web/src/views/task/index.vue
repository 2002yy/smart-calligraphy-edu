<script setup lang="ts">
import { computed } from "vue";

import { useTeacherStore } from "../../stores/teacher";
import AppSkeleton from "../../components/AppSkeleton.vue";
import CollapsibleIntro from "../../components/CollapsibleIntro.vue";
import type { Classroom, Course, Task, TaskForm } from "../../types";

const store = useTeacherStore();

const props = defineProps<{
  loading?: boolean;
  courses: Course[];
  classes: Classroom[];
  tasks: Task[];
  form: TaskForm;
  submitting: boolean;
}>();

const emit = defineEmits<{
  "update:form": [value: TaskForm];
  submit: [];
}>();

const localForm = computed({
  get: () => props.form,
  set: (value: TaskForm) => emit("update:form", value)
});

function updateField<K extends keyof TaskForm>(key: K, value: TaskForm[K]) {
  emit("update:form", { ...props.form, [key]: value });
}

function hasCourseError() {
  return props.courses.length > 0 && !props.form.course_id;
}

function hasClassError() {
  return props.classes.length > 0 && !props.form.class_id;
}

function hasTitleError() {
  return !props.form.title.trim();
}

function hasPracticeCharsError() {
  return !props.form.practiceChars.trim();
}

function confirmDelete(task: Task) {
  if (confirm(`确定删除任务"${task.title}"？`)) {
    store.deleteTask(task.id);
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">任务编排</p>
        <h2>把教学目标写成可执行的训练任务</h2>
      </div>
      <button class="primary-btn" :disabled="submitting" @click="$emit('submit')">
        <span class="btn-content">
          <span v-if="submitting" class="btn-spinner"></span>
          {{ submitting ? "发布中..." : "发布任务" }}
        </span>
      </button>
    </div>

    <CollapsibleIntro storageKey="intro-task">
      在这里发布训练任务，明确告诉学生"练什么、怎么评、何时交"，让每一次练习都有清晰的目标。
    </CollapsibleIntro>

    <div v-if="loading && !courses.length && !tasks.length" class="task-layout">
      <section class="editor-shell skeleton-shell">
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="2" />
        <AppSkeleton :lines="4" />
      </section>

      <section class="preview-shell skeleton-shell">
        <AppSkeleton :lines="3" />
        <AppSkeleton :lines="3" />
        <AppSkeleton :lines="3" />
      </section>
    </div>

    <div v-else class="task-layout">
      <form class="editor-shell" @submit.prevent="$emit('submit')">
        <div class="section-head">
          <h3>任务配置</h3>
          <span>编辑区</span>
        </div>

        <label class="field-block">
          <span>所属课程</span>
          <select
            :value="localForm.course_id ?? ''"
            @change="updateField('course_id', Number(($event.target as HTMLSelectElement).value) || null)"
          >
            <option value="">请选择课程</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
          <small v-if="hasCourseError()" class="validation-error">发布任务前请先选择课程。</small>
        </label>

        <label class="field-block">
          <span>所属班级</span>
          <select
            :value="localForm.class_id ?? ''"
            @change="updateField('class_id', Number(($event.target as HTMLSelectElement).value) || null)"
          >
            <option value="">请选择班级</option>
            <option v-for="classItem in classes" :key="classItem.id" :value="classItem.id">
              {{ classItem.name }}
            </option>
          </select>
          <small v-if="hasClassError()" class="validation-error">发布任务前请先选择班级。</small>
        </label>

        <label class="field-block">
          <span>任务标题</span>
          <input
            :value="localForm.title"
            type="text"
            placeholder="例如：欧楷结构与重心训练"
            @input="updateField('title', ($event.target as HTMLInputElement).value)"
          />
          <small v-if="hasTitleError()" class="validation-error">任务标题不能为空。</small>
        </label>

        <label class="field-block">
          <span>练习字</span>
          <input
            :value="localForm.practiceChars"
            type="text"
            placeholder="例如：永、木、中、人"
            @input="updateField('practiceChars', ($event.target as HTMLInputElement).value)"
          />
          <small v-if="hasPracticeCharsError()" class="validation-error">请至少填写一个练习字。</small>
        </label>

        <label class="field-block">
          <span>截止时间</span>
          <input
            :value="localForm.deadline"
            type="datetime-local"
            @input="updateField('deadline', ($event.target as HTMLInputElement).value)"
          />
        </label>

        <label class="field-block full-row">
          <span>任务说明</span>
          <textarea
            :value="localForm.description"
            rows="5"
            placeholder="例如：重点观察结构均衡与重心稳定，按时提交书写作品。"
            @input="updateField('description', ($event.target as HTMLTextAreaElement).value)"
          />
        </label>

        <section class="weight-block">
          <strong>当前评分维度</strong>
          <div class="weight-row">
            <span>结构布局 40%</span>
            <span>重心控制 30%</span>
            <span>笔顺规范 30%</span>
          </div>
        </section>
      </form>

      <section class="preview-shell">
        <div class="section-head">
          <h3>已发布任务</h3>
          <span>{{ tasks.length }} 条</span>
        </div>

        <div v-if="tasks.length" class="task-list">
          <article v-for="task in tasks" :key="task.id" class="task-record">
            <div class="record-head">
              <strong>{{ task.title }}</strong>
              <span>
                #{{ task.id }}
                <button class="delete-btn" type="button" title="删除任务" @click="confirmDelete(task)">✕</button>
              </span>
            </div>
            <p>{{ task.description || "暂无任务说明。" }}</p>
            <div class="record-meta">
              <small>练习字：{{ task.practice_chars.join("、") }}</small>
              <small>课程 {{ task.course_id }} / 班级 {{ task.class_id }}</small>
            </div>
          </article>
        </div>
        <p v-else class="muted-copy">当前还没有发布任务，可以先用左侧表单完成第一条训练任务。</p>
      </section>
    </div>

    <section class="after-block">
      <strong>下一步建议</strong>
      <p>任务发布完成后，学生就可以在"学生端"提交作品并触发 AI 评测，教师可以在看板和批阅页看到结果。</p>
    </section>
  </section>
</template>

<style scoped>
.task-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  gap: 28px;
}

.editor-shell,
.preview-shell {
  display: grid;
  gap: 14px;
  align-content: start;
}

.skeleton-shell {
  min-height: 400px;
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

.field-block {
  display: grid;
  gap: 8px;
}

.field-block span {
  color: var(--muted);
  font-size: 13px;
}

.full-row {
  width: 100%;
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

.weight-block {
  display: grid;
  gap: 10px;
  margin-top: 6px;
  padding-top: 14px;
  border-top: 1px solid rgba(78, 53, 34, 0.1);
}

.weight-block strong {
  font-size: 15px;
}

.weight-row {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  color: var(--muted);
}

.task-list {
  display: grid;
  gap: 14px;
}

.task-record {
  padding: 14px 0;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.task-record:last-child {
  border-bottom: none;
}

.record-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.record-head strong {
  font-size: 17px;
}

.record-head span {
  color: var(--accent-deep);
  font-size: 13px;
}

.task-record p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.record-meta {
  display: grid;
  gap: 4px;
  margin-top: 10px;
  color: var(--muted);
}

.delete-btn {
  margin-left: 8px;
  border: none;
  background: transparent;
  color: #b5442b;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
}
.delete-btn:hover {
  background: rgba(181, 68, 43, 0.1);
}

.muted-copy {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
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
  .task-layout {
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
