<script setup lang="ts">
import { storeToRefs } from "pinia";

import AppSkeleton from "../components/AppSkeleton.vue";
import CollapsibleIntro from "../components/CollapsibleIntro.vue";
import PageState from "../components/PageState.vue";
import { useStudentStore } from "../stores/student";

const store = useStudentStore();
const { user, loading, tasks, selectedTaskId, selectedTask } = storeToRefs(store);
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">任务中心</p>
        <h2>明确任务，再开始练习</h2>
      </div>
      <span class="badge">{{ tasks.length }} 项任务</span>
    </div>

    <CollapsibleIntro storageKey="intro-task">
      左侧列出任务列表，右侧展示任务详情，包括练习字、评分维度和截止时间。
    </CollapsibleIntro>

    <div v-if="loading && !tasks.length" class="task-layout">
      <section class="task-list skeleton-shell">
        <AppSkeleton :lines="3" />
        <AppSkeleton :lines="3" />
        <AppSkeleton :lines="3" />
      </section>
      <section class="task-detail skeleton-shell">
        <AppSkeleton :lines="5" />
      </section>
    </div>

    <PageState
      v-else-if="!user"
      mode="empty"
      title="请先登录后查看任务"
      description="登录学生账号后，系统会自动展示当前班级下的训练任务。"
      compact
    />

    <PageState
      v-else-if="!tasks.length"
      mode="empty"
      title="当前班级还没有任务"
      description="可以先在教师端发布训练任务，再回到这里刷新查看。"
      compact
    />

    <div v-else class="task-layout">
      <section class="task-list">
        <button
          v-for="task in tasks"
          :key="task.id"
          class="task-row"
          :class="{ active: task.id === selectedTaskId }"
          @click="store.selectTask(task.id)"
        >
          <strong>{{ task.title }}</strong>
          <small>练习字：{{ task.practice_chars.join("、") }}</small>
        </button>
      </section>

      <section class="task-detail">
        <template v-if="selectedTask">
          <div class="section-head">
            <h3>{{ selectedTask.title }}</h3>
            <span>任务详情</span>
          </div>
          <div class="reading-line">
            <b>{{ selectedTask.practice_chars.join("、") }}</b>
            <span>练习字</span>
          </div>
          <div class="reading-line">
            <b>
              结构 {{ selectedTask.structure_weight }} / 重心 {{ selectedTask.center_weight }} / 笔顺
              {{ selectedTask.stroke_order_weight }}
            </b>
            <span>评分权重</span>
          </div>
          <div class="reading-line">
            <b>{{ selectedTask.deadline || "未设置" }}</b>
            <span>截止时间</span>
          </div>
          <p class="detail-copy">{{ selectedTask.description || "暂无任务说明。" }}</p>
        </template>
        <p v-else class="muted-copy">选择一个任务后，这里会显示详细训练说明。</p>
      </section>
    </div>
  </section>
</template>

<style scoped>
.task-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.86fr) minmax(0, 1.14fr);
  gap: 24px;
}

.task-list,
.task-detail {
  display: grid;
  align-content: start;
}

.task-list {
  gap: 10px;
}

.skeleton-shell {
  min-height: 320px;
}

.task-row {
  display: grid;
  gap: 6px;
  text-align: left;
  padding: 14px 0;
  border: none;
  border-bottom: 1px solid rgba(21, 66, 90, 0.1);
  background: transparent;
}

.task-row strong {
  font-size: 17px;
  color: var(--ink);
}

.task-row small {
  color: var(--muted);
}

.task-row.active strong {
  color: var(--accent-deep);
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.section-head h3 {
  margin: 0;
  font-size: 24px;
}

.section-head span {
  color: var(--accent-deep);
  font-size: 13px;
}

.reading-line {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px dashed rgba(21, 66, 90, 0.12);
}

.reading-line:last-of-type {
  border-bottom: none;
}

.reading-line b {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.8;
}

.reading-line span,
.muted-copy,
.detail-copy {
  color: var(--muted);
}

.reading-line span {
  text-align: right;
}

.detail-copy,
.muted-copy {
  margin: 14px 0 0;
  line-height: 1.8;
}

@media (max-width: 1280px) {
  .task-layout {
    grid-template-columns: 1fr;
  }
}
</style>

