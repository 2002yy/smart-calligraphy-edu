<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";

import AnimatedCount from "../components/AnimatedCount.vue";
import AppSkeleton from "../components/AppSkeleton.vue";
import CollapsibleIntro from "../components/CollapsibleIntro.vue";
import PageState from "../components/PageState.vue";
import TrendChart from "../components/TrendChart.vue";
import { useStudentStore } from "../stores/student";

const store = useStudentStore();
const { user, loading, growth, classes, latestHomework, evaluation } = storeToRefs(store);

const recentScores = computed(() => growth.value?.recent_scores ?? []);
const recentLabels = computed(() => growth.value?.recent_labels ?? []);
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">成长档案</p>
        <h2>把每一次练习沉淀成可解释的成长</h2>
      </div>
      <span class="badge">学生个人画像</span>
    </div>

    <CollapsibleIntro storageKey="intro-growth">
      成长档案不是"成绩展示页"，而是用来说明系统如何持续记录学习过程、提炼问题标签，并形成阶段性的个性化反馈。
    </CollapsibleIntro>

    <template v-if="loading && !growth">
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
      title="请先登录后查看成长档案"
      description="登录学生账号后，系统会自动展示最近作业、评测摘要与成长数据。"
    />

    <template v-else>
      <div class="metric-strip">
        <article class="metric-block accent" style="--i: 0">
          <span>平均得分</span>
          <AnimatedCount :value="growth?.avg_score ?? 0" />
          <small>基于历史评测结果动态计算。</small>
        </article>
        <article class="metric-block" style="--i: 1">
          <span>参与班级数</span>
          <AnimatedCount :value="classes.length" />
          <small>体现当前学习场景覆盖情况。</small>
        </article>
        <article class="metric-block" style="--i: 2">
          <span>最近作业</span>
          <strong>{{ latestHomework?.id ?? "--" }}</strong>
          <small>方便答辩时解释最近一次联调记录。</small>
        </article>
      </div>

      <section class="trend-section" v-if="recentScores.length >= 2">
        <div class="section-head">
          <h3>评分趋势</h3>
          <span>历史变化</span>
        </div>
        <div class="trend-body">
          <TrendChart :scores="recentScores" :labels="recentLabels" />
        </div>
      </section>

      <div class="story-grid">
        <section class="story-block">
          <div class="section-head">
            <h3>最近一次评测摘要</h3>
            <span>阶段反馈</span>
          </div>
          <div class="reading-line">
            <b>{{ evaluation?.total_score ?? "--" }}</b>
            <span>总分</span>
          </div>
          <div class="reading-line">
            <b>{{ evaluation?.issues?.join("、") || "暂无" }}</b>
            <span>问题标签</span>
          </div>
          <div class="reading-line">
            <b>{{ evaluation?.advice || "完成评测后会出现更具体的练习建议。" }}</b>
            <span>建议摘要</span>
          </div>
        </section>

        <section class="story-block">
          <div class="section-head">
            <h3>答辩可讲重点</h3>
            <span>PPT 话术</span>
          </div>
          <ul class="speech-list">
            <li>学生端不是一次性任务展示，而是把任务、提交、评测和成长沉淀串成完整学习路径。</li>
            <li>平均分和问题标签可以作为阶段性学习结果，为教师后续因材施教提供依据。</li>
            <li>这一页适合强调系统在"数据留痕"和"个性化反馈"上的产品价值。</li>
          </ul>
        </section>
      </div>
    </template>
  </section>
</template>

<style scoped>
.story-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
  margin-top: 26px;
}

.story-block {
  display: grid;
  gap: 12px;
}

.skeleton-story {
  min-height: 220px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 4px;
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

.reading-line:last-child {
  border-bottom: none;
}

.reading-line b {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.8;
}

.reading-line span,
.speech-list {
  color: var(--muted);
}

.reading-line span {
  text-align: right;
}

.speech-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.9;
}

.trend-section {
  margin-top: 26px;
}

.trend-body {
  padding: 16px 0 8px;
}

@media (max-width: 1280px) {
  .metric-strip,
  .story-grid {
    grid-template-columns: 1fr;
  }
}
</style>
