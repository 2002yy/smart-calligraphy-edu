<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onShow(() => {
  if (studentStore.token) {
    studentStore.refresh();
  }
});

function startToday() {
  if (studentStore.todayTask) {
    studentStore.openTask(studentStore.todayTask.id);
  } else {
    uni.switchTab({ url: "/pages/task/list" });
  }
}
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="welcome">你好，{{ studentStore.user?.name || "同学" }}</text>
      <text class="title">今天继续把每一笔写稳。</text>
      <text class="subtitle">{{ studentStore.message }}</text>
      <button class="primary-button hero-button" @tap="startToday">
        {{ studentStore.todayTask ? "开始今日练习" : "查看任务列表" }}
      </button>
    </view>

    <view class="stats section">
      <view class="stat-card">
        <text class="stat-value">{{ studentStore.tasks.length }}</text>
        <text class="stat-label">待练任务</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ studentStore.avgScore || "--" }}</text>
        <text class="stat-label">平均分</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ studentStore.history.length }}</text>
        <text class="stat-label">历史作品</text>
      </view>
    </view>

    <view v-if="studentStore.todayTask" class="card section task-card" @tap="studentStore.openTask(studentStore.todayTask.id)">
      <text class="card-label">今日推荐</text>
      <text class="task-title">{{ studentStore.todayTask.title }}</text>
      <text class="task-desc">{{ studentStore.todayTask.description || "完成练习后可上传作品进行 AI 评分。" }}</text>
      <view class="char-row">
        <text v-for="char in studentStore.todayTask.practice_chars" :key="char" class="char-box">{{ char }}</text>
      </view>
    </view>

    <view v-else class="card section join-card">
      <text class="card-label">加入班级</text>
      <text class="task-title">输入老师提供的邀请码</text>
      <text class="task-desc">加入班级后，老师发布的练习任务会同步到任务列表。</text>
      <input v-model="studentStore.inviteCode" class="invite-input" placeholder="例如 CALLI2026" />
      <button class="secondary-button join-button" :loading="studentStore.joining" @tap="studentStore.joinClass">加入班级</button>
    </view>
  </view>
</template>

<style scoped>
.hero {
  padding: 36rpx 0 10rpx;
}

.welcome {
  display: block;
  margin-bottom: 18rpx;
  font-size: 28rpx;
  color: #4b5563;
}

.hero-button {
  margin-top: 32rpx;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18rpx;
}

.stat-card {
  min-height: 132rpx;
  border-radius: 16rpx;
  background: #ffffff;
  padding: 22rpx;
}

.stat-value {
  display: block;
  font-size: 42rpx;
  font-weight: 800;
  color: #111827;
}

.stat-label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #6b7280;
}

.card-label {
  font-size: 24rpx;
  color: #6366f1;
  font-weight: 700;
}

.task-title {
  display: block;
  margin-top: 12rpx;
  font-size: 34rpx;
  font-weight: 800;
  color: #111827;
}

.task-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  line-height: 1.6;
  color: #6b7280;
}

.char-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 22rpx;
}

.char-box {
  min-width: 64rpx;
  height: 64rpx;
  border-radius: 12rpx;
  background: #f3f4f6;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 64rpx;
  text-align: center;
}

.invite-input {
  height: 84rpx;
  margin-top: 24rpx;
  border-radius: 14rpx;
  background: #f3f4f6;
  padding: 0 24rpx;
  font-size: 28rpx;
}

.join-button {
  margin-top: 18rpx;
}
</style>
