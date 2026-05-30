<script setup lang="ts">
import AnimatedCount from "../../components/AnimatedCount.vue";
import AppSkeleton from "../../components/AppSkeleton.vue";
import CollapsibleIntro from "../../components/CollapsibleIntro.vue";
import PageState from "../../components/PageState.vue";
import type { ClassReport, DashboardData } from "../../types";

defineProps<{
  dashboard: DashboardData | null;
  report: ClassReport | null;
  activeClassName: string;
  loading: boolean;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">教学看板</p>
        <h2>{{ activeClassName || "请选择班级" }}</h2>
      </div>
      <span class="badge">{{ loading ? "同步中" : "已连接" }}</span>
    </div>

    <CollapsibleIntro storageKey="intro-dashboard">
      这一页不是简单的数据堆叠，而是教师复盘课堂的起点。建议答辩时从"班级整体状态"讲起，再过渡到共性问题与报告摘要，形成完整的教学闭环叙事。
    </CollapsibleIntro>

    <template v-if="loading && !dashboard">
      <div class="metric-strip">
        <article v-for="index in 4" :key="`metric-${index}`" class="metric-block skeleton-block">
          <AppSkeleton :lines="2" compact />
        </article>
      </div>

      <div class="narrative-grid">
        <section v-for="index in 2" :key="`detail-${index}`" class="story-block skeleton-story">
          <AppSkeleton :lines="5" />
        </section>
      </div>
    </template>

    <template v-else-if="dashboard">
      <div class="metric-strip">
        <article class="metric-block accent" style="--i: 0">
          <span>班级平均分</span>
          <AnimatedCount :value="dashboard.avg_score" />
          <small>用于说明当前班级整体书写表现。</small>
        </article>
        <article class="metric-block" style="--i: 1">
          <span>作业提交率</span>
          <strong>{{ Math.round(dashboard.submit_rate * 100) }}%</strong>
          <small>反映学生参与度和任务完成度。</small>
        </article>
        <article class="metric-block" style="--i: 2">
          <span>累计作业数</span>
          <AnimatedCount :value="dashboard.homework_count" />
          <small>表示已进入系统的作品总量。</small>
        </article>
        <article class="metric-block" style="--i: 3">
          <span>已完成评测</span>
          <AnimatedCount :value="dashboard.evaluated_count" />
          <small>体现智能评测的回流覆盖情况。</small>
        </article>
      </div>

      <div class="narrative-grid">
        <section class="story-block">
          <div class="section-head">
            <h3>班级整体状态</h3>
            <span>课堂概况</span>
          </div>
          <div class="reading-list">
            <div class="reading-line">
              <b>{{ dashboard.student_count }}</b>
              <span>当前班级学生人数</span>
            </div>
            <div class="reading-line">
              <b>{{ dashboard.task_count }}</b>
              <span>教师已发布训练任务</span>
            </div>
            <div class="reading-line">
              <b>{{ dashboard.class_name }}</b>
              <span>正在查看的统计对象</span>
            </div>
          </div>
        </section>

        <section class="story-block">
          <div class="section-head">
            <h3>共性问题与报告摘要</h3>
            <span>复盘重点</span>
          </div>

          <div class="subsection">
            <strong>共性问题</strong>
            <ul v-if="dashboard.top_issues.length" class="issue-list">
              <li v-for="issue in dashboard.top_issues" :key="issue">{{ issue }}</li>
            </ul>
            <p v-else class="muted-copy">当前暂无稳定的共性问题标签。</p>
          </div>

          <div class="subsection">
            <strong>报告摘要</strong>
            <div v-if="report" class="reading-list compact">
              <div class="reading-line">
                <b>{{ report.student_count }}</b>
                <span>报告统计学生人数</span>
              </div>
              <div class="reading-line">
                <b>{{ report.task_count }}</b>
                <span>报告统计任务数量</span>
              </div>
              <div class="reading-line">
                <b>{{ report.homework_count }}</b>
                <span>已累计作业量</span>
              </div>
              <div class="reading-line">
                <b>{{ report.avg_score }}</b>
                <span>报告平均分</span>
              </div>
            </div>
            <p v-else class="muted-copy">选择班级后，系统会自动同步报告摘要。</p>
          </div>
        </section>
      </div>
    </template>

    <PageState
      v-else-if="!loading"
      mode="empty"
      title="还没有可展示的班级看板"
      description="请先登录教师账号，并在左侧选择课程和班级，系统才会生成教学看板与统计摘要。"
    />
  </section>
</template>

<style scoped>
.metric-strip {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.narrative-grid {
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
}

.story-block {
  padding-top: 8px;
}

.skeleton-story {
  min-height: 240px;
}

.section-head {
  margin-bottom: 18px;
}

.reading-list {
  display: grid;
  gap: 10px;
}

.reading-list.compact {
  gap: 8px;
}

.reading-line b {
  font-size: 18px;
}

.reading-line span {
  color: var(--muted);
  text-align: right;
}

.subsection + .subsection {
  margin-top: 24px;
}

.subsection strong {
  display: block;
  margin-bottom: 10px;
  font-size: 15px;
}

.issue-list {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.9;
}

.muted-copy {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

@media (max-width: 1280px) {
  .metric-strip,
  .narrative-grid {
    grid-template-columns: 1fr;
  }
}
</style>
