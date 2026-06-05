<script setup lang="ts">
import { computed, ref } from "vue";

import AppSkeleton from "../../components/AppSkeleton.vue";
import CollapsibleIntro from "../../components/CollapsibleIntro.vue";
import PageState from "../../components/PageState.vue";
import type { Review } from "../../types";

const props = defineProps<{
  reviews: Review[];
  loading: boolean;
}>();

const statusFilter = ref<"all" | "reviewed" | "pending">("all");
const aiFilter = ref<"all" | "with-ai" | "without-ai">("all");
const activeReviewId = ref<number | null>(null);

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const filteredReviews = computed(() =>
  props.reviews.filter((review) => {
    const matchesStatus =
      statusFilter.value === "all"
        ? true
        : statusFilter.value === "reviewed"
          ? review.status === "reviewed"
          : review.status !== "reviewed";

    const hasAiResult = review.score !== null && review.score !== undefined;
    const matchesAi =
      aiFilter.value === "all"
        ? true
        : aiFilter.value === "with-ai"
          ? hasAiResult
          : !hasAiResult;

    return matchesStatus && matchesAi;
  })
);

const activeReview = computed(() => filteredReviews.value.find((review) => review.id === activeReviewId.value) || null);

function normalizeAssetUrl(url?: string | null) {
  if (!url) {
    return "";
  }

  if (/^https?:\/\//.test(url)) {
    return url;
  }

  return `${apiBaseUrl}${url.startsWith("/") ? url : `/${url}`}`;
}

function toggleDrawer(reviewId: number) {
  activeReviewId.value = activeReviewId.value === reviewId ? null : reviewId;
}

function closeDrawer() {
  activeReviewId.value = null;
}

function formatDate(value?: string | null) {
  if (!value) {
    return "待同步";
  }

  return new Date(value).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">批阅复盘</p>
        <h2>把 AI 初评、作业上下文和教师复核放进同一条批阅链路</h2>
      </div>
      <span class="badge">{{ loading ? "同步中" : `${filteredReviews.length} 条记录` }}</span>
    </div>

    <CollapsibleIntro storageKey="intro-review">
      查看学生提交的作业、AI 评分结果和教师评语，完成作业批阅与反馈。
    </CollapsibleIntro>

    <section class="filter-bar">
      <label class="filter-item">
        <span>作业状态</span>
        <select v-model="statusFilter">
          <option value="all">全部状态</option>
          <option value="reviewed">已批阅</option>
          <option value="pending">待补评</option>
        </select>
      </label>

      <label class="filter-item">
        <span>AI 结果</span>
        <select v-model="aiFilter">
          <option value="all">全部</option>
          <option value="with-ai">已有 AI 初评</option>
          <option value="without-ai">暂无 AI 初评</option>
        </select>
      </label>
    </section>

    <div v-if="loading && !reviews.length" class="review-list">
      <article v-for="item in 3" :key="item" class="review-line skeleton-line">
        <AppSkeleton :lines="4" />
      </article>
    </div>

    <div v-else-if="filteredReviews.length" class="review-list">
      <article v-for="review in filteredReviews" :key="review.id" class="review-line">
        <div class="review-thumb-wrap">
          <img
            v-if="normalizeAssetUrl(review.compare_image_url || review.image_url)"
            :src="normalizeAssetUrl(review.compare_image_url || review.image_url)"
            alt=""
            class="review-thumb"
            loading="lazy"
          />
          <div v-else class="review-thumb-empty">
            <span>暂无图片</span>
          </div>
        </div>

        <div class="review-body">
          <div class="review-top">
            <div class="review-meta">
              <strong>{{ review.task_title || `作业 #${review.homework_id}` }}</strong>
              <span>
                {{ review.student_name || `学生 ${review.student_id ?? "--"}` }}
                ·
                {{ review.homework_status || review.status }}
              </span>
            </div>

            <div class="score-pair">
              <div class="score-block">
                <span>AI 初评</span>
                <b>{{ review.score ?? "--" }}</b>
              </div>
              <div class="score-block accent">
                <span>教师终评</span>
                <b>{{ review.final_score ?? "--" }}</b>
              </div>
            </div>
          </div>

          <div class="review-scores" v-if="review.structure_score != null">
            <div class="mini-score"><span>结构</span><b>{{ review.structure_score }}</b></div>
            <div class="mini-score"><span>重心</span><b>{{ review.center_score }}</b></div>
            <div class="mini-score"><span>笔法</span><b>{{ review.stroke_order_score }}</b></div>
          </div>

          <div class="review-grid">
            <section class="review-copy">
              <strong>AI 建议</strong>
              <p>{{ review.advice || "当前还没有同步到 AI 建议。" }}</p>
            </section>

            <section class="review-copy">
              <strong>问题标签</strong>
              <ul class="tag-list">
                <li v-for="tag in review.tags?.length ? review.tags : ['暂无标签']" :key="tag">{{ tag }}</li>
              </ul>
            </section>

            <section class="review-copy teacher-copy">
              <strong>教师评语</strong>
              <p>{{ review.comment || "当前尚未填写教师评语。" }}</p>
              <small>{{ formatDate(review.reviewed_at) }}</small>
            </section>
          </div>

          <div class="detail-row">
            <div class="context-pills">
              <span class="context-pill">任务 {{ review.task_id ?? "--" }}</span>
              <span class="context-pill">作业 {{ review.homework_id }}</span>
              <span class="context-pill">提交 {{ formatDate(review.submitted_at) }}</span>
            </div>

            <button class="ghost-btn detail-btn" type="button" @click="toggleDrawer(review.id)">
              {{ activeReviewId === review.id ? "收起详情" : "展开查看详情" }}
            </button>
          </div>
        </div>
      </article>
    </div>

    <PageState
      v-else
      mode="empty"
      :title="reviews.length ? '筛选后暂无匹配记录' : '当前还没有批阅记录'"
      :description="
        reviews.length
          ? '可以切换作业状态或 AI 结果筛选条件，查看不同阶段的教学反馈。'
          : '学生完成作业提交并生成评分结果后，教师端会在这里同步看到 AI 初评、教师复核和批阅上下文。'
      "
      compact
    />

    <transition name="drawer-fade">
      <div v-if="activeReview" class="drawer-mask" @click.self="closeDrawer">
        <aside class="drawer-panel">
          <div class="drawer-head">
            <div>
              <p class="eyebrow">批阅详情</p>
              <h3>{{ activeReview.task_title || `作业 #${activeReview.homework_id}` }}</h3>
            </div>
            <button class="close-btn" type="button" @click="closeDrawer">关闭</button>
          </div>

          <div class="drawer-content">
            <section class="drawer-visual">
              <div class="drawer-image-frame">
                <img
                  v-if="normalizeAssetUrl(activeReview.compare_image_url || activeReview.image_url)"
                  :src="normalizeAssetUrl(activeReview.compare_image_url || activeReview.image_url)"
                  alt="作业详情图"
                />
                <div v-else class="drawer-image-empty">暂无可预览图片</div>
              </div>
              <p class="drawer-caption">
                {{ activeReview.compare_image_url ? "评测回看图" : "学生提交原图" }}
              </p>
            </section>

            <section class="drawer-context">
              <article class="context-block">
                <span>学生</span>
                <strong>{{ activeReview.student_name || `学生 ${activeReview.student_id ?? "--"}` }}</strong>
              </article>
              <article class="context-block">
                <span>作业状态</span>
                <strong>{{ activeReview.homework_status || activeReview.status }}</strong>
              </article>
              <article class="context-block">
                <span>提交时间</span>
                <strong>{{ formatDate(activeReview.submitted_at) }}</strong>
              </article>
              <article class="context-block">
                <span>批阅时间</span>
                <strong>{{ formatDate(activeReview.reviewed_at) }}</strong>
              </article>
            </section>

            <section class="drawer-section">
              <strong>AI 评分摘要</strong>
              <div class="drawer-metrics">
                <article>
                  <span>AI 初评</span>
                  <b>{{ activeReview.score ?? "--" }}</b>
                </article>
                <article>
                  <span>教师终评</span>
                  <b>{{ activeReview.final_score ?? "--" }}</b>
                </article>
              </div>
              <div class="drawer-sub-scores" v-if="activeReview.structure_score != null">
                <article><span>结构</span><b>{{ activeReview.structure_score }}</b></article>
                <article><span>重心</span><b>{{ activeReview.center_score }}</b></article>
                <article><span>笔法</span><b>{{ activeReview.stroke_order_score }}</b></article>
              </div>
            </section>

            <section class="drawer-section" v-if="activeReview.thinking_steps?.length">
              <strong>AI 思考过程</strong>
              <div class="thinking-steps-compact">
                <div v-for="step in activeReview.thinking_steps" :key="step.step" class="ts-item">
                  <span class="ts-step">{{ step.step }}.</span>
                  <span class="ts-title">{{ step.title }}</span>
                  <span v-if="step.score != null" class="ts-score">{{ step.score }}</span>
                </div>
              </div>
            </section>

            <section class="drawer-section">
              <strong>问题标签</strong>
              <ul class="tag-list">
                <li v-for="tag in activeReview.tags?.length ? activeReview.tags : ['暂无标签']" :key="tag">{{ tag }}</li>
              </ul>
            </section>

            <section class="drawer-section">
              <strong>AI 建议</strong>
              <p>{{ activeReview.advice || "当前还没有 AI 建议。" }}</p>
            </section>

            <section class="drawer-section">
              <strong>教师评语</strong>
              <p>{{ activeReview.comment || "当前尚未填写教师评语。" }}</p>
            </section>
          </div>
        </aside>
      </div>
    </transition>
  </section>
</template>

<style scoped>
.filter-bar {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 240px));
  gap: 14px;
  margin-bottom: 22px;
}

.filter-item {
  display: grid;
  gap: 8px;
}

.filter-item span {
  color: var(--muted);
  font-size: 13px;
}

.review-list {
  display: grid;
  gap: 18px;
}

.review-line {
  display: flex;
  gap: 18px;
  padding: 18px 0 22px;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.review-line:last-child {
  border-bottom: none;
}

.review-thumb-wrap {
  flex-shrink: 0;
  width: 120px;
  height: 90px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(78, 53, 34, 0.1);
  background: rgba(248, 239, 227, 0.6);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: zoom-in;
}

.review-thumb-wrap:hover {
  transform: scale(2.2);
  box-shadow: 0 8px 32px rgba(46, 27, 12, 0.2);
  z-index: 10;
  position: relative;
}

.review-thumb {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.review-thumb-empty {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  color: var(--muted);
  font-size: 11px;
}

.review-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 18px;
}

.review-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
}

.review-meta {
  display: grid;
  gap: 6px;
}

.review-meta strong {
  font-size: 18px;
}

.review-meta span {
  color: var(--muted);
}

.score-pair {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
}

.score-block {
  display: grid;
  gap: 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(78, 53, 34, 0.12);
}

.score-block.accent {
  border-bottom-color: rgba(180, 97, 49, 0.28);
}

.score-block span {
  color: var(--muted);
  font-size: 13px;
}

.score-block b {
  font-size: 28px;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.review-copy {
  display: grid;
  gap: 8px;
}

.review-copy strong {
  font-size: 15px;
}

.review-copy p,
.review-copy small {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.teacher-copy {
  padding-left: 16px;
  border-left: 1px solid rgba(78, 53, 34, 0.08);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding-top: 4px;
}

.context-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.context-pill,
.tag-list li {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(180, 97, 49, 0.08);
  color: var(--accent-deep);
  font-size: 13px;
}

.detail-btn {
  min-width: 148px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.skeleton-line {
  min-height: 160px;
}

.drawer-mask {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgba(34, 23, 15, 0.26);
  backdrop-filter: blur(6px);
}

.drawer-panel {
  width: min(640px, 100%);
  height: 100%;
  padding: 28px 24px 24px;
  background:
    linear-gradient(180deg, rgba(255, 251, 244, 0.98), rgba(251, 243, 230, 0.98)),
    repeating-linear-gradient(
      180deg,
      rgba(120, 78, 41, 0.04) 0,
      rgba(120, 78, 41, 0.04) 1px,
      transparent 1px,
      transparent 28px
    );
  box-shadow: -18px 0 46px rgba(46, 27, 12, 0.18);
  overflow-y: auto;
}

.drawer-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.drawer-head h3 {
  margin: 4px 0 0;
  font-size: 32px;
  line-height: 1.16;
}

.close-btn {
  min-width: 88px;
  min-height: 42px;
  border: 1px solid rgba(78, 53, 34, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--ink);
  cursor: pointer;
}

.drawer-content {
  display: grid;
  gap: 22px;
  padding-top: 22px;
}

.drawer-visual {
  display: grid;
  gap: 12px;
}

.drawer-image-frame {
  overflow: hidden;
  min-height: 260px;
  border-radius: 28px;
  border: 1px solid rgba(78, 53, 34, 0.1);
  background:
    linear-gradient(180deg, rgba(253, 248, 240, 0.92), rgba(248, 239, 227, 0.88)),
    repeating-linear-gradient(
      180deg,
      rgba(120, 78, 41, 0.04) 0,
      rgba(120, 78, 41, 0.04) 1px,
      transparent 1px,
      transparent 28px
    );
}

.drawer-image-frame img {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 260px;
  object-fit: contain;
}

.drawer-image-empty {
  display: grid;
  place-items: center;
  min-height: 260px;
  color: var(--muted);
}

.drawer-caption,
.drawer-section p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.drawer-context {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.context-block {
  display: grid;
  gap: 6px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.context-block span {
  color: var(--muted);
  font-size: 13px;
}

.context-block strong {
  font-size: 18px;
}

.drawer-section {
  display: grid;
  gap: 10px;
}

.drawer-section strong {
  font-size: 16px;
}

.drawer-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.drawer-metrics article {
  display: grid;
  gap: 8px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(78, 53, 34, 0.1);
}

.drawer-metrics span {
  color: var(--muted);
  font-size: 13px;
}

.drawer-metrics b {
  font-size: 30px;
}

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.24s ease;
}

.drawer-fade-enter-active .drawer-panel,
.drawer-fade-leave-active .drawer-panel {
  transition: transform 0.28s ease, opacity 0.24s ease;
}

.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

.drawer-fade-enter-from .drawer-panel,
.drawer-fade-leave-to .drawer-panel {
  transform: translateX(24px);
  opacity: 0;
}

/* 子维度分数（批阅卡片上） */
.review-scores {
  display: flex;
  gap: 10px;
  padding-bottom: 10px;
}
.mini-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 14px;
  border-radius: 10px;
  background: rgba(180, 97, 49, 0.06);
}
.mini-score span {
  font-size: 11px;
  color: var(--muted);
}
.mini-score b {
  font-size: 20px;
  color: var(--accent-deep);
}

/* 子维度分数（抽屉内） */
.drawer-sub-scores {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}
.drawer-sub-scores article {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 0;
  border-radius: 12px;
  background: rgba(180, 97, 49, 0.06);
}
.drawer-sub-scores span {
  font-size: 12px;
  color: var(--muted);
}
.drawer-sub-scores b {
  font-size: 24px;
  color: var(--accent-deep);
}

/* AI 思考过程（抽屉内紧凑版） */
.thinking-steps-compact {
  display: grid;
  gap: 4px;
  padding-top: 6px;
}
.ts-item {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 4px 0;
  font-size: 13px;
}
.ts-step {
  color: var(--muted);
  min-width: 18px;
  text-align: right;
}
.ts-title {
  flex: 1;
  color: var(--ink);
}
.ts-score {
  font-weight: 600;
  color: var(--accent-deep);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1280px) {
  .review-line {
    flex-direction: column;
  }

  .review-thumb-wrap {
    width: 100%;
    height: 140px;
  }

  .review-thumb-wrap:hover {
    transform: none;
    box-shadow: none;
  }

  .review-top,
  .review-grid,
  .score-pair,
  .filter-bar,
  .drawer-context,
  .drawer-metrics {
    grid-template-columns: 1fr;
    display: grid;
  }

  .teacher-copy {
    padding-left: 0;
    border-left: none;
  }

  .detail-row {
    align-items: start;
    flex-direction: column;
  }
}
</style>
