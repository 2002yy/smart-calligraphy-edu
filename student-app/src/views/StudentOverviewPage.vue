<script setup lang="ts">
import { storeToRefs } from "pinia";

import AnimatedCount from "../components/AnimatedCount.vue";
import AppSkeleton from "../components/AppSkeleton.vue";
import CollapsibleIntro from "../components/CollapsibleIntro.vue";
import PageState from "../components/PageState.vue";
import { useStudentStore } from "../stores/student";

const store = useStudentStore();
const { user, loading, classes, tasks, growth, selectedTask, latestHomework, evaluation } = storeToRefs(store);
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">学习总览</p>
        <h2>先看路径，再进入动作</h2>
      </div>
      <span class="badge">学生端首页</span>
    </div>

    <CollapsibleIntro storageKey="intro-overview">
      这里展示你的班级数量、当前任务数和平均得分，快速了解学习状态。
    </CollapsibleIntro>

    <template v-if="loading">
      <div class="metric-strip">
        <article v-for="index in 3" :key="`summary-${index}`" class="metric-block skeleton-block">
          <AppSkeleton :lines="2" compact />
        </article>
      </div>

      <div class="story-grid">
        <section v-for="index in 2" :key="`detail-${index}`" class="story-block skeleton-story">
          <AppSkeleton :lines="5" />
        </section>
      </div>
    </template>

    <PageState
      v-else-if="!user"
      mode="empty"
      title="还没有进入学习空间"
      description="请先在左侧登录学生账号，系统会自动同步班级、任务与最近一次学习记录。"
    />

    <template v-else>
      <div class="metric-strip">
        <article class="metric-block accent" style="--i: 0">
          <span>已加入班级</span>
          <AnimatedCount :value="classes.length" />
          <small>当前可参与学习的班级数量。</small>
        </article>
        <article class="metric-block" style="--i: 1">
          <span>当前任务数</span>
          <AnimatedCount :value="tasks.length" />
          <small>所选班级下可练习的任务数。</small>
        </article>
        <article class="metric-block" style="--i: 2">
          <span>平均得分</span>
          <AnimatedCount :value="growth?.avg_score ?? 0" />
          <small>根据历史评测结果动态更新。</small>
        </article>
      </div>

      <div class="story-grid">
        <section class="story-block">
          <div class="section-head">
            <h3>当前推荐任务</h3>
            <span>今天练什么</span>
          </div>
          <template v-if="selectedTask">
            <div class="reading-line">
              <b>{{ selectedTask.title }}</b>
              <span>任务标题</span>
            </div>
            <div class="reading-line">
              <b>{{ selectedTask.practice_chars.join("、") }}</b>
              <span>练习字</span>
            </div>
            <div class="reading-line">
              <b>{{ selectedTask.description || "暂无任务说明" }}</b>
              <span>任务说明</span>
            </div>
          </template>
          <p v-else class="muted-copy">当前还没有可练习任务，请先选择班级或等待教师发布任务。</p>
        </section>

        <section class="story-block">
          <div class="section-head">
            <h3>最近一次学习反馈</h3>
            <span>最近反馈</span>
          </div>
          <div class="reading-line">
            <b>{{ latestHomework?.status || "暂无提交记录" }}</b>
            <span>作业状态</span>
          </div>
          <div class="reading-line">
            <b>{{ evaluation?.total_score ?? "--" }}</b>
            <span>最近得分</span>
          </div>
          <div class="reading-line">
            <b>{{ evaluation?.advice || "完成 AI 评测后将显示针对性建议" }}</b>
            <span>建议摘要</span>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>
