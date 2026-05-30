<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { storeToRefs } from "pinia";

import AppSkeleton from "../components/AppSkeleton.vue";
import CollapsibleIntro from "../components/CollapsibleIntro.vue";
import PageState from "../components/PageState.vue";
import ScoreRing from "../components/ScoreRing.vue";
import { useStudentStore } from "../stores/student";
import type { ThinkingStep } from "../types";

const store = useStudentStore();
const { user, loading, selectedTask, submitForm, latestHomework, evaluation, submitting, evaluating, quickEvaluating, previewUrl } =
  storeToRefs(store);

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const uploadStage = computed(() => {
  if (quickEvaluating.value || evaluating.value) {
    return "evaluating";
  }

  if (evaluation.value) {
    return "review";
  }

  if (latestHomework.value) {
    return "uploaded";
  }

  return "idle";
});

const resultImageUrl = computed(() => {
  const source = evaluation.value?.compare_image_url || latestHomework.value?.image_url || "";
  if (!source) {
    return "";
  }

  if (/^https?:\/\//.test(source)) {
    return source;
  }

  return `${apiBaseUrl}${source.startsWith("/") ? source : `/${source}`}`;
});

// ---- Thinking chain animation ----
// Timing config (ms) — varies by provider for realistic pacing
const STEP_RUNNING_MS: Record<string, number> = { mock: 500, openai: 1200, qwen: 1200, auto: 800 };
const STEP_GAP_MS: Record<string, number> = { mock: 120, openai: 350, qwen: 350, auto: 200 };

const localThinkingSteps = ref<ThinkingStep[]>([]);
const thinkingExpanded = ref(true);
const chainVisible = ref(false);
const currentProvider = computed(() => {
  // 默认用 "qwen" 动画效果（与按钮保持一致）
  return "qwen";
});
let animationActive = false;
let animationTimers: number[] = [];

watch(evaluating, (isEvaluating) => {
  if (isEvaluating) {
    chainVisible.value = true;
    startThinkingAnimation(currentProvider.value);
  } else if (!isEvaluating && !evaluation.value) {
    stopAnimation();
    chainVisible.value = false;
  }
});

watch(evaluation, (evalData) => {
  if (evalData) {
    stopAnimation();
    localThinkingSteps.value =
      evalData.thinking_steps?.length > 0
        ? evalData.thinking_steps
        : localThinkingSteps.value.map((s) => ({ ...s, status: "done" as const }));
    thinkingExpanded.value = true;
  }
});

onBeforeUnmount(stopAnimation);

function stopAnimation() {
  animationActive = false;
  animationTimers.forEach(clearTimeout);
  animationTimers = [];
}

function startThinkingAnimation(provider = "auto") {
  stopAnimation();
  const runMs = STEP_RUNNING_MS[provider] ?? STEP_RUNNING_MS.auto;
  const gapMs = STEP_GAP_MS[provider] ?? STEP_GAP_MS.auto;

  const mockSteps: ThinkingStep[] = [
    { step: 1, title: "图像预处理", detail: "正在加载书法作业图像...", status: "pending" },
    { step: 2, title: "文字区域检测", detail: "检测练习字区域...", status: "pending" },
    { step: 3, title: "单字分割", detail: "分割单字区域...", status: "pending" },
    { step: 4, title: "结构分析", detail: "分析字形结构...", status: "pending" },
    { step: 5, title: "重心检测", detail: "检测书写重心...", status: "pending" },
    { step: 6, title: "笔顺验证", detail: "验证笔画顺序...", status: "pending" },
    { step: 7, title: "综合评分", detail: "生成最终评分...", status: "pending" },
  ];
  localThinkingSteps.value = mockSteps;
  animationActive = true;
  thinkingExpanded.value = true;
  chainVisible.value = true;
  let stepIndex = 0;

  const revealNext = () => {
    if (!animationActive || stepIndex >= mockSteps.length) return;
    const copy = [...localThinkingSteps.value];
    copy[stepIndex] = { ...copy[stepIndex], status: "running" };
    localThinkingSteps.value = copy;

    const t1 = window.setTimeout(() => {
      if (!animationActive) return;
      const copy2 = [...localThinkingSteps.value];
      copy2[stepIndex] = { ...copy2[stepIndex], status: "done" };
      localThinkingSteps.value = copy2;
      stepIndex++;
      const t2 = window.setTimeout(revealNext, gapMs);
      animationTimers.push(t2);
    }, runMs);
    animationTimers.push(t1);
  };

  revealNext();
}
// ---- end thinking chain ----

function hasFileError() {
  return !submitForm.value.selectedFileName?.trim();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0] || null;
  store.updateSelectedFile(file);
}
</script>

<template>
  <section class="panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">提交评测</p>
        <h2>把上传、评测和结果回看组织成一条清晰的学生动作路径</h2>
      </div>
      <span class="badge">学生端主闭环</span>
    </div>

    <CollapsibleIntro storageKey="intro-submit">
      这一页不只是"传一张图"，而是把学生完成任务后的关键反馈组织成完整过渡：先上传作品，再确认提交成功，最后进入评测结果回看。
    </CollapsibleIntro>

    <div v-if="loading && !user && !selectedTask && !latestHomework" class="submit-layout">
      <section class="editor-shell skeleton-shell">
        <AppSkeleton :lines="5" />
      </section>
      <section class="result-shell skeleton-shell">
        <AppSkeleton :lines="5" />
      </section>
    </div>

    <PageState
      v-else-if="!user"
      mode="empty"
      title="请先登录后提交作业"
      description="登录学生账号并选择任务后，这里会显示提交区、状态过渡和评测结果回看区。"
    />

    <PageState
      v-else-if="!selectedTask && !latestHomework"
      mode="empty"
      title="还没有可提交的任务"
      description="请先到任务中心选择本周练习任务，再回到这里完成上传与评测。"
    />

    <div v-else class="submit-layout">
      <section class="editor-shell">
        <div class="section-head">
          <h3>作品提交</h3>
          <span>学生动作</span>
        </div>

        <div v-if="selectedTask" class="focus-block">
          <strong>{{ selectedTask.title }}</strong>
          <small>练习字：{{ selectedTask.practice_chars.join("、") }}</small>
        </div>

        <label class="field-block">
          <span>选择作业图片</span>
          <input type="file" accept="image/*" @change="handleFileChange" />
          <small class="field-hint">系统会先上传原图，再生成作业记录，确保学生端、教师端和 AI 评分读取同一份作品。</small>
          <small v-if="submitForm.selectedFileName" class="field-hint">当前文件：{{ submitForm.selectedFileName }}</small>
          <small v-if="submitForm.imageUrl" class="field-hint">已上传地址：{{ submitForm.imageUrl }}</small>
          <small v-if="hasFileError()" class="validation-error">请先选择一张作业图片。</small>
        </label>

        <transition name="preview-switch" mode="out-in">
          <section v-if="uploadStage === 'idle' && previewUrl" key="local-preview" class="preview-block">
            <strong>本地预览</strong>
            <div class="preview-frame">
              <img :src="previewUrl" alt="作业图片预览" />
            </div>
          </section>

          <section v-else-if="uploadStage === 'uploaded'" key="upload-success" class="status-stage success-stage">
            <div class="status-mark">
              <span class="ring"></span>
              <span class="dot">✓</span>
            </div>
            <div class="status-copy">
              <strong>上传成功，作品已进入系统</strong>
              <p>现在可以直接触发 Qwen AI 评分，系统会在右侧生成可回看的评测结果图和练习建议。</p>
            </div>
          </section>

          <section v-else-if="uploadStage === 'evaluating'" key="evaluating-stage" class="status-stage evaluating-stage">
            <div class="status-mark pulse">
              <span class="ring"></span>
              <span class="dot">评</span>
            </div>
            <div class="status-copy">
              <strong>正在分析结构、重心与笔势</strong>
              <p>系统正在生成评分结果，请稍候查看总分、问题标签和结果回看图。</p>
            </div>
          </section>

          <section v-else-if="uploadStage === 'review' && resultImageUrl" key="result-review" class="preview-block">
            <strong>结果回看图</strong>
            <div class="preview-frame result-frame">
              <img :src="resultImageUrl" alt="评测结果回看图" />
            </div>
            <small class="field-hint">上传预览已自动切换为结果回看图，方便答辩时展示"提交后如何被系统分析"。</small>
          </section>
        </transition>

        <div class="action-stack">
          <button class="hero-btn" :disabled="quickEvaluating || submitting || evaluating" @click="store.submitAndEvaluateWithQwen()">
            <span class="btn-content">
              <span v-if="quickEvaluating" class="btn-spinner white"></span>
              <svg v-else class="hero-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 1.5v3M10 15.5v3M4.22 4.22l2.12 2.12M13.66 13.66l2.12 2.12M1.5 10h3M15.5 10h3M4.22 15.78l2.12-2.12M13.66 6.34l2.12-2.12"/>
              </svg>
              {{ quickEvaluating ? "提交并评测中..." : "提交后触发 Qwen AI 评分" }}
            </span>
          </button>

          <button class="secondary-btn" :disabled="submitting || quickEvaluating" @click="store.submitAndEvaluateWithOpenAI()">
            <span class="btn-content">
              <span v-if="submitting && !quickEvaluating" class="btn-spinner"></span>
              {{ submitting && !quickEvaluating ? "提交中..." : "提交 + 旧版 GPT 评测" }}
            </span>
          </button>

          <button class="secondary-btn" :disabled="submitting || quickEvaluating" @click="store.submitHomework()">
            <span class="btn-content">
              <span v-if="submitting && !quickEvaluating" class="btn-spinner"></span>
              {{ submitting && !quickEvaluating ? "提交中..." : "仅提交作业" }}
            </span>
          </button>

          <button class="ghost-btn" :disabled="evaluating || !latestHomework || quickEvaluating" @click="store.evaluateHomework()">
            <span class="btn-content">
              <span v-if="evaluating && !quickEvaluating" class="btn-spinner dark"></span>
              {{ evaluating && !quickEvaluating ? "评测中..." : "对最近一次作业发起评测" }}
            </span>
          </button>
        </div>

        <p v-if="latestHomework" class="muted-copy">最近一次作业：#{{ latestHomework.id }}，当前状态：{{ latestHomework.status }}</p>
      </section>

      <Transition name="chain-switch" mode="out-in">
        <PageState
          v-if="(evaluating || quickEvaluating) && !evaluation && !chainVisible"
          key="loading"
          mode="loading"
          title="正在生成评分结果"
          description="系统正在分析结构、重心和笔画表现，请稍候查看分数、标签与练习建议。"
          compact
        />

        <section
          v-else-if="(evaluating || quickEvaluating) && !evaluation && chainVisible"
          key="evaluating"
          class="result-shell"
        >
          <div class="thinking-chain">
            <div class="thinking-header">
              <div class="thinking-header-left">
                <span class="thinking-icon">⟐</span>
                <span>思考过程</span>
                <span class="step-count">
                  {{ localThinkingSteps.filter((s) => s.status === "done").length }}/{{ localThinkingSteps.length }}
                </span>
              </div>
            </div>
            <div class="steps-list">
              <div
                v-for="step in localThinkingSteps"
                :key="step.step"
                class="step-item"
                :class="`step-${step.status}`"
              >
                <div class="step-indicator">
                  <span v-if="step.status === 'pending'" class="step-circle pending">
                    <span class="pending-dot"></span>
                  </span>
                  <span v-else-if="step.status === 'running'" class="step-circle running">
                    <span class="running-spinner"></span>
                  </span>
                  <span v-else class="step-circle done"><span class="checkmark">✓</span></span>
                  <span v-if="step.step < localThinkingSteps.length" class="step-line" :class="{ 'line-done': step.status === 'done' }"></span>
                </div>
                <div class="step-body">
                  <div class="step-title">{{ step.title }}</div>
                  <div v-if="step.detail" class="step-detail">{{ step.detail }}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-else-if="evaluation" key="results" class="result-shell">
          <div class="section-head">
            <h3>评分结果</h3>
            <span>即时反馈</span>
          </div>

          <!-- collapsible thinking chain -->
          <div v-if="localThinkingSteps.length" class="thinking-chain done-chain">
            <div class="thinking-header" @click="thinkingExpanded = !thinkingExpanded">
              <div class="thinking-header-left">
                <span class="thinking-icon">⟐</span>
                <span>思考过程</span>
                <span class="step-count">{{ localThinkingSteps.filter((s) => s.status === "done").length }}/{{ localThinkingSteps.length }}</span>
              </div>
              <span class="toggle-icon">{{ thinkingExpanded ? "收起" : "展开" }}</span>
            </div>
            <TransitionGroup v-if="thinkingExpanded" name="step-fade" tag="div" class="steps-list">
              <div
                v-for="step in localThinkingSteps"
                :key="step.step"
                class="step-item step-done"
              >
                <div class="step-indicator">
                  <span class="step-circle done"><span class="checkmark">✓</span></span>
                  <span v-if="step.step < localThinkingSteps.length" class="step-line line-done"></span>
                </div>
                <div class="step-body">
                  <div class="step-title">{{ step.title }}</div>
                  <div v-if="step.detail" class="step-detail">{{ step.detail }}</div>
                </div>
                <div v-if="step.score != null" class="step-score">{{ step.score }}</div>
              </div>
            </TransitionGroup>
          </div>

          <div class="score-grid">
            <article class="score-card primary">
              <ScoreRing :score="evaluation.score ?? evaluation.total_score" label="总分" :size="104" :stroke-width="7" />
            </article>
            <article class="score-card">
              <ScoreRing :score="evaluation.structure_score" label="结构" :delay="120" />
            </article>
            <article class="score-card">
              <ScoreRing :score="evaluation.center_score" label="重心" :delay="240" />
            </article>
            <article class="score-card">
              <ScoreRing :score="evaluation.stroke_order_score" label="笔画" :delay="360" />
            </article>
          </div>

          <section class="result-copy">
            <strong>练习建议</strong>
            <p>{{ evaluation.advice || "当前暂无练习建议。" }}</p>
          </section>

          <section class="result-copy">
            <strong>问题标签</strong>
            <ul class="issue-list">
              <li v-for="issue in evaluation.tags?.length ? evaluation.tags : evaluation.issues" :key="issue">{{ issue }}</li>
            </ul>
          </section>
        </section>

        <PageState
          v-else
          key="empty"
          mode="empty"
          title="评分结果会显示在这里"
          description="先提交作业，再触发评测，系统会在这里生成分数、标签和练习建议。"
          compact
        />
      </Transition>
    </div>
  </section>
</template>

<style scoped>
.submit-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.84fr) minmax(0, 1.16fr);
  gap: 24px;
}

.editor-shell,
.result-shell {
  display: grid;
  gap: 14px;
  align-content: start;
}

.skeleton-shell {
  min-height: 320px;
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

.focus-block {
  display: grid;
  gap: 4px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(21, 66, 90, 0.1);
}

.focus-block small {
  color: var(--muted);
}

.field-block {
  display: grid;
  gap: 8px;
}

.field-block span {
  color: var(--muted);
  font-size: 13px;
}

.field-hint,
.muted-copy {
  color: var(--muted);
}

.preview-block {
  display: grid;
  gap: 10px;
}

.preview-block strong,
.status-copy strong {
  font-size: 15px;
}

.preview-frame {
  overflow: hidden;
  border: 1px solid rgba(21, 66, 90, 0.12);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(248, 252, 255, 0.9), rgba(238, 246, 250, 0.88)),
    repeating-linear-gradient(
      180deg,
      rgba(21, 66, 90, 0.04) 0,
      rgba(21, 66, 90, 0.04) 1px,
      transparent 1px,
      transparent 28px
    );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.result-frame {
  border-color: rgba(43, 151, 202, 0.18);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 20px 48px rgba(32, 108, 144, 0.12);
}

.preview-frame img {
  display: block;
  width: 100%;
  max-height: 320px;
  object-fit: contain;
}

.status-stage {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  min-height: 180px;
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(21, 66, 90, 0.1);
  background:
    linear-gradient(180deg, rgba(248, 252, 255, 0.9), rgba(236, 246, 251, 0.88)),
    repeating-linear-gradient(
      180deg,
      rgba(21, 66, 90, 0.04) 0,
      rgba(21, 66, 90, 0.04) 1px,
      transparent 1px,
      transparent 28px
    );
}

.success-stage {
  box-shadow: 0 18px 42px rgba(43, 151, 202, 0.12);
}

.evaluating-stage {
  box-shadow: 0 18px 42px rgba(21, 66, 90, 0.1);
}

.status-mark {
  position: relative;
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
}

.status-mark .ring,
.status-mark .dot {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}

.status-mark .ring {
  border: 1px solid rgba(43, 151, 202, 0.22);
  animation: breathe 1.8s ease-in-out infinite;
}

.status-mark .dot {
  inset: 10px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #15425a 0%, #2b97ca 100%);
  color: #ffffff;
  font-size: 24px;
  font-weight: 700;
  box-shadow: 0 12px 28px rgba(32, 108, 144, 0.22);
}

.pulse .dot {
  animation: pulse 1.1s ease-in-out infinite;
}

.status-copy {
  display: grid;
  gap: 8px;
}

.status-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.validation-error {
  color: #b5442b;
  font-size: 12px;
  line-height: 1.6;
}

.action-stack {
  display: grid;
  gap: 10px;
}

.ghost-btn {
  min-height: 46px;
  border: 1px solid rgba(21, 66, 90, 0.15);
  background: rgba(255, 255, 255, 0.7);
  color: var(--ink);
  border-radius: 999px;
  font-size: 15px;
  cursor: pointer;
}

.accent-btn {
  background: linear-gradient(135deg, #15425a 0%, #2b97ca 100%);
}

/* ---- score rings ---- */
.score-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 8px 0 16px;
}

.score-card {
  display: grid;
  place-items: center;
  padding: 18px 8px;
  border-radius: 20px;
  border: 1px solid rgba(21, 66, 90, 0.08);
  background: linear-gradient(180deg, rgba(252, 254, 255, 0.96), rgba(240, 249, 255, 0.92));
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.score-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(21, 66, 90, 0.08);
}

.score-card.primary {
  border-color: rgba(43, 151, 202, 0.18);
  box-shadow: 0 4px 16px rgba(43, 151, 202, 0.08);
}

/* ---- hero button ---- */
.hero-btn {
  position: relative;
  overflow: hidden;
  min-height: 54px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #15425a 0%, #2b97ca 100%);
  color: #ffffff;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(43, 151, 202, 0.28);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hero-btn::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    120deg,
    rgba(255, 255, 255, 0) 30%,
    rgba(255, 255, 255, 0.18) 50%,
    rgba(255, 255, 255, 0) 70%
  );
  transform: translateX(-100%);
  animation: hero-shine 3s ease-in-out infinite;
}

.hero-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(43, 151, 202, 0.35);
}

.hero-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

.hero-btn:disabled::after {
  animation: none;
}

.hero-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.secondary-btn {
  min-height: 46px;
  border: 1px solid rgba(21, 66, 90, 0.2);
  background: rgba(255, 255, 255, 0.6);
  color: var(--ink);
  border-radius: 999px;
  font-size: 15px;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease;
}

.secondary-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.secondary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
}

.btn-spinner.white {
  border-color: rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  width: 16px;
  height: 16px;
}

.result-copy {
  display: grid;
  gap: 8px;
  padding-top: 8px;
}

.result-copy strong {
  font-size: 15px;
}

.result-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.issue-list {
  margin: 0;
  padding-left: 18px;
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

.btn-spinner.dark {
  border-color: rgba(21, 66, 90, 0.2);
  border-top-color: #15425a;
}

.preview-switch-enter-active,
.preview-switch-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.preview-switch-enter-from,
.preview-switch-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* chain cross-fade transition */
.chain-switch-enter-active,
.chain-switch-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.chain-switch-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.chain-switch-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 1280px) {
  .submit-layout,
  .metric-strip,
  .score-grid,
  .status-stage {
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

@keyframes hero-shine {
  0% {
    transform: translateX(-100%);
  }
  20% {
    transform: translateX(100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes breathe {
  0%,
  100% {
    transform: scale(0.96);
    opacity: 0.6;
  }

  50% {
    transform: scale(1.08);
    opacity: 1;
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.06);
  }
}

/* ===== thinking chain ===== */
.thinking-chain {
  display: grid;
  gap: 2px;
  border-radius: 20px;
  border: 1px solid rgba(21, 66, 90, 0.1);
  background: linear-gradient(180deg, rgba(248, 252, 255, 0.92), rgba(238, 246, 250, 0.88));
  padding: 18px 16px;
  box-shadow: 0 4px 16px rgba(21, 66, 90, 0.06);
}

.thinking-chain.done-chain {
  margin-bottom: 16px;
}

.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
}

.thinking-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink, #1a2e3a);
}

.thinking-icon {
  font-size: 18px;
  opacity: 0.65;
}

.step-count {
  font-size: 12px;
  font-weight: 400;
  color: var(--muted, #6a7e8a);
  background: rgba(21, 66, 90, 0.08);
  padding: 2px 8px;
  border-radius: 999px;
}

.toggle-icon {
  font-size: 13px;
  color: var(--muted, #6a7e8a);
}

.steps-list {
  display: grid;
  gap: 0;
  padding-top: 12px;
}

.step-item {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  gap: 12px;
  padding: 6px 0;
  min-height: 40px;
  align-items: start;
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.step-pending {
  opacity: 0.35;
}

.step-running {
  opacity: 1;
}

.step-done {
  opacity: 1;
}

.step-indicator {
  display: grid;
  justify-items: center;
  align-items: start;
  gap: 2px;
  padding-top: 3px;
}

.step-circle {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.step-circle.pending {
  border: 2px solid rgba(21, 66, 90, 0.18);
  background: transparent;
}

.pending-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(21, 66, 90, 0.2);
}

.step-circle.running {
  border: 2px solid rgba(43, 151, 202, 0.3);
  background: rgba(43, 151, 202, 0.08);
  animation: step-running-pulse 1s ease-in-out infinite;
}

.running-spinner {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #2b97ca;
  animation: step-running-dot 0.8s ease-in-out infinite;
}

.step-circle.done {
  background: linear-gradient(135deg, #15425a, #2b97ca);
  border: none;
}

.checkmark {
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
}

.step-line {
  width: 2px;
  min-height: 28px;
  flex: 1;
  background: rgba(21, 66, 90, 0.1);
  border-radius: 1px;
}

.step-line.line-done {
  background: linear-gradient(180deg, #2b97ca, rgba(43, 151, 202, 0.3));
}

.step-body {
  display: grid;
  gap: 2px;
  padding-top: 2px;
  min-height: 36px;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink, #1a2e3a);
}

.step-detail {
  font-size: 12px;
  color: var(--muted, #6a7e8a);
  line-height: 1.6;
  max-width: 36rem;
}

.step-score {
  font-size: 16px;
  font-weight: 700;
  color: #2b97ca;
  padding-top: 2px;
  font-variant-numeric: tabular-nums;
}

/* transition-group fade */
.step-fade-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.step-fade-leave-active {
  transition: opacity 0.15s ease;
}

.step-fade-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}

.step-fade-leave-to {
  opacity: 0;
}

@keyframes step-running-pulse {
  0%, 100% {
    border-color: rgba(43, 151, 202, 0.3);
    box-shadow: 0 0 0 0 rgba(43, 151, 202, 0.1);
  }
  50% {
    border-color: rgba(43, 151, 202, 0.6);
    box-shadow: 0 0 0 6px rgba(43, 151, 202, 0);
  }
}

@keyframes step-running-dot {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.7;
  }
}
</style>
