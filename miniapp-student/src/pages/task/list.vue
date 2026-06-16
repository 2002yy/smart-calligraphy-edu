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
    <text class="title">Practice tasks</text>
    <text class="subtitle">Choose a task, upload your work, and get an AI score.</text>

    <view class="section task-list">
      <view v-for="task in studentStore.tasks" :key="task.id" class="card task-item" @tap="studentStore.openTask(task.id)">
        <view>
          <text class="task-title">{{ task.title }}</text>
          <text class="task-desc">{{ task.description || "No task description yet." }}</text>
        </view>
        <view class="char-row">
          <text v-for="char in task.practice_chars" :key="`${task.id}-${char}`" class="char-box">{{ char }}</text>
        </view>
      </view>
    </view>

    <view v-if="!studentStore.tasks.length" class="card section empty">
      <text class="empty-title">No tasks yet</text>
      <text class="empty-desc">For this test build, join class with invite code CALLI2026.</text>
      <input v-model="studentStore.inviteCode" class="invite-input" placeholder="CALLI2026" />
      <button class="secondary-button join-button" :loading="studentStore.joining" @tap="studentStore.joinClass">Join class</button>
    </view>
  </view>
</template>

<style scoped>
.task-list {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.task-item {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.task-title {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
  color: #111827;
}

.task-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 25rpx;
  line-height: 1.55;
  color: #6b7280;
}

.char-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.char-box {
  min-width: 58rpx;
  height: 58rpx;
  border-radius: 12rpx;
  background: #f3f4f6;
  font-size: 28rpx;
  font-weight: 800;
  line-height: 58rpx;
  text-align: center;
}

.empty-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #111827;
}

.empty-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  line-height: 1.5;
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
