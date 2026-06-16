<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onShow(() => {
  if (studentStore.token) {
    studentStore.refresh().catch((error) => {
      studentStore.setMessage(error instanceof Error ? error.message : "Refresh failed. Check backend service.");
    });
  }
});
</script>

<template>
  <view class="page">
    <view class="profile-head">
      <view class="avatar">{{ (studentStore.user?.name || "S").slice(0, 1) }}</view>
      <view>
        <text class="title">{{ studentStore.user?.name || "Student" }}</text>
        <text class="subtitle">Test build account: student01 / 123456</text>
      </view>
    </view>

    <view class="card section demo-card">
      <text class="block-title">Test build reminder</text>
      <text class="muted-text">Invite code for this demo: CALLI2026</text>
      <text class="muted-text">If no tasks appear after login, join the class here.</text>
    </view>

    <view class="card section">
      <text class="block-title">Progress</text>
      <view class="progress-row">
        <text>Average score</text>
        <text class="strong">{{ studentStore.avgScore || "--" }}</text>
      </view>
      <view class="progress-row">
        <text>Submitted works</text>
        <text class="strong">{{ studentStore.history.length }}</text>
      </view>
      <view class="progress-row">
        <text>Tasks</text>
        <text class="strong">{{ studentStore.tasks.length }}</text>
      </view>
    </view>

    <view class="card section">
      <text class="block-title">Recent scores</text>
      <view v-if="studentStore.progress?.recent_scores?.length" class="score-strip">
        <view v-for="(score, index) in studentStore.progress.recent_scores" :key="index" class="score-pill">
          <text>{{ Math.round(score * 10) }}</text>
        </view>
      </view>
      <text v-else class="muted-text">No score records yet.</text>
    </view>

    <view class="card section">
      <text class="block-title">Join class</text>
      <text class="muted-text">Test invite code: CALLI2026</text>
      <input v-model="studentStore.inviteCode" class="invite-input" placeholder="CALLI2026" />
      <button class="secondary-button join-button" :loading="studentStore.joining" @tap="studentStore.joinClass">Join class</button>
    </view>

    <button class="secondary-button section" @tap="studentStore.logout">Logout</button>
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

.demo-card {
  background: #eef2ff;
  box-shadow: none;
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
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #6b7280;
}

.invite-input {
  height: 84rpx;
  margin-top: 22rpx;
  border-radius: 14rpx;
  background: #f3f4f6;
  padding: 0 24rpx;
  font-size: 28rpx;
}

.join-button {
  margin-top: 18rpx;
}
</style>
