<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onShow(() => {
  if (studentStore.token) {
    studentStore.refresh();
  }
});
</script>

<template>
  <view class="page">
    <view class="profile-head">
      <view class="avatar">{{ (studentStore.user?.name || "学").slice(0, 1) }}</view>
      <view>
        <text class="title">{{ studentStore.user?.name || "学生" }}</text>
        <text class="subtitle">{{ studentStore.user?.school_name || "智慧书法练习档案" }}</text>
      </view>
    </view>

    <view class="card section">
      <text class="block-title">成长档案</text>
      <view class="progress-row">
        <text>平均分</text>
        <text class="strong">{{ studentStore.avgScore || "--" }}</text>
      </view>
      <view class="progress-row">
        <text>提交作品</text>
        <text class="strong">{{ studentStore.history.length }}</text>
      </view>
      <view class="progress-row">
        <text>待练任务</text>
        <text class="strong">{{ studentStore.tasks.length }}</text>
      </view>
    </view>

    <view class="card section">
      <text class="block-title">最近分数</text>
      <view v-if="studentStore.progress?.recent_scores?.length" class="score-strip">
        <view v-for="(score, index) in studentStore.progress.recent_scores" :key="index" class="score-pill">
          <text>{{ Math.round(score * 10) }}</text>
        </view>
      </view>
      <text v-else class="muted-text">暂无评分记录。</text>
    </view>

    <button class="secondary-button section" @tap="studentStore.logout">退出登录</button>
  </view>
</template>

<style scoped>
.profile-head {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding-top: 32rpx;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  flex: 0 0 112rpx;
  border-radius: 28rpx;
  background: #111827;
  color: #ffffff;
  font-size: 44rpx;
  font-weight: 900;
  line-height: 112rpx;
  text-align: center;
}

.block-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.progress-row {
  display: flex;
  justify-content: space-between;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #edf0f4;
  font-size: 28rpx;
}

.progress-row:last-child {
  border-bottom: 0;
}

.strong {
  font-weight: 900;
  color: #111827;
}

.score-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.score-pill {
  min-width: 76rpx;
  height: 58rpx;
  border-radius: 999rpx;
  background: #eef2ff;
  color: #3730a3;
  font-size: 28rpx;
  font-weight: 800;
  line-height: 58rpx;
  text-align: center;
}

.muted-text {
  font-size: 26rpx;
  color: #6b7280;
}
</style>
