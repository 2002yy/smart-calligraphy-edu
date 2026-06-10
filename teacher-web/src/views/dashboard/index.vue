<script setup lang="ts">
import { useRouter } from "vue-router";
import AnimatedCount from "../../components/AnimatedCount.vue";
import AppSkeleton from "../../components/AppSkeleton.vue";
import CollapsibleIntro from "../../components/CollapsibleIntro.vue";
import PageState from "../../components/PageState.vue";
import type { ClassReport, DashboardData } from "../../types";

const router = useRouter();

defineProps<{
  dashboard: DashboardData | null;
  report: ClassReport | null;
  activeClassName: string;
  loading: boolean;
}>();

function navigateToReviews(tag: string) {
  router.push({ path: "/reviews", query: { tag } });
}
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
      这里展示班级整体学习状态，包括作业提交率、平均得分和共性问题，方便教师跟进教学效果。
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
          <small>班级整体书写表现的平均分。</small>
        </article>
        <article class="metric-block" style="--i: 1">
          <span>作业提交率</span>
          <strong>{{ Math.round(dashboard.submit_rate * 100) }}%</strong>
          <small>学生参与度和任务完成情况。</small>
        </article>
        <article class="metric-block" style="--i: 2">
          <span>累计作业数</span>
          <AnimatedCount :value="dashboard.homework_count" />
          <small>学生提交到系统的作业总数。</small>
        </article>
        <article class="metric-block" style="--i: 3">
          <span>已完成评测</span>
          <AnimatedCount :value="dashboard.evaluated_count" />
          <small>已经完成智能评测的作业数量。</small>
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

          <div class="subsection" v-if="dashboard.top_issue_tags?.length">
            <strong>常见问题标签 Top {{ Math.min(dashboard.top_issue_tags.length, 8) }}</strong>
            <div class="tag-chip-group">
              <button
                v-for="tag in dashboard.top_issue_tags.slice(0, 8)"
                :key="tag"
                class="tag-chip issue"
                @click="navigateToReviews(tag)"
                :title="`筛选「${tag}」的作业`"
              >
                {{ tag }}
              </button>
            </div>
          </div>

          <div class="subsection" v-if="dashboard.top_positive_tags?.length">
            <strong>优秀表现标签 Top {{ Math.min(dashboard.top_positive_tags.length, 5) }}</strong>
            <div class="tag-chip-group">
              <button
                v-for="tag in dashboard.top_positive_tags.slice(0, 5)"
                :key="tag"
                class="tag-chip positive"
                @click="navigateToReviews(tag)"
                :title="`筛选「${tag}」的作业`"
              >
                {{ tag }}
              </button>
            </div>
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

.tag-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 13px;
  transition: transform 0.15s, box-shadow 0.15s;
}

.tag-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
}

.tag-chip.issue {
  background: rgba(220, 80, 60, 0.08);
  color: #b84a38;
  border-color: rgba(220, 80, 60, 0.2);
}

.tag-chip.positive {
  background: rgba(60, 160, 80, 0.08);
  color: #2e7d46;
  border-color: rgba(60, 160, 80, 0.2);
}

@media (max-width: 1280px) {
  .metric-strip,
  .narrative-grid {
    grid-template-columns: 1fr;
  }
}
</style>
