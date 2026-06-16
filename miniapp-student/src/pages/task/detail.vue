<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onLoad((query) => {
  const id = Number(query?.id);
  if (id) {
    studentStore.loadTask(id);
  }
});

function goSubmit() {
  if (studentStore.selectedTask) {
    uni.navigateTo({ url: `/pages/submit/index?id=${studentStore.selectedTask.id}` });
  }
}
</script>

<template>
  <view class="page">
    <view v-if="studentStore.selectedTask" class="detail">
      <text class="title">{{ studentStore.selectedTask.title }}</text>
      <text class="subtitle">{{ studentStore.selectedTask.description || "请根据任务字帖完成本次练习。" }}</text>

      <view class="card section">
        <text class="block-title">练习字</text>
        <view class="char-grid">
          <text v-for="char in studentStore.selectedTask.practice_chars" :key="char" class="char-box">{{ char }}</text>
        </view>
      </view>

      <view class="card section">
        <text class="block-title">评分维度</text>
        <view class="score-row">
          <text>结构</text>
          <text>{{ studentStore.selectedTask.structure_weight }}%</text>
        </view>
        <view class="score-row">
          <text>重心</text>
          <text>{{ studentStore.selectedTask.center_weight }}%</text>
        </view>
        <view class="score-row">
          <text>笔法</text>
          <text>{{ studentStore.selectedTask.stroke_order_weight }}%</text>
        </view>
      </view>

      <button class="primary-button section" @tap="goSubmit">拍照上传作品</button>
    </view>
  </view>
</template>

<style scoped>
.block-title {
  display: block;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: #111827;
}

.char-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}

.char-box {
  aspect-ratio: 1;
  border-radius: 14rpx;
  background: #f3f4f6;
  font-size: 52rpx;
  font-weight: 800;
  line-height: 132rpx;
  text-align: center;
}

.score-row {
  display: flex;
  justify-content: space-between;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #edf0f4;
  font-size: 28rpx;
}

.score-row:last-child {
  border-bottom: 0;
}
</style>
