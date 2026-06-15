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
    <text class="title">练习任务</text>
    <text class="subtitle">选择一个任务，查看要求后拍照上传作品。</text>

    <view class="section task-list">
      <view v-for="task in studentStore.tasks" :key="task.id" class="card task-item" @tap="studentStore.openTask(task.id)">
        <view>
          <text class="task-title">{{ task.title }}</text>
          <text class="task-desc">{{ task.description || "暂无任务说明" }}</text>
        </view>
        <view class="char-row">
          <text v-for="char in task.practice_chars" :key="`${task.id}-${char}`" class="char-box">{{ char }}</text>
        </view>
      </view>
    </view>

    <view v-if="!studentStore.tasks.length" class="card section empty">
      <text>当前没有练习任务，请等待老师发布。</text>
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

.empty {
  font-size: 28rpx;
  color: #6b7280;
}
</style>
