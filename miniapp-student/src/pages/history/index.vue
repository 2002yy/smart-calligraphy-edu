<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onShow(() => {
  if (studentStore.token) {
    studentStore.refresh();
  }
});

function openResult(homeworkId: number) {
  uni.navigateTo({ url: `/pages/result/index?id=${homeworkId}` });
}
</script>

<template>
  <view class="page">
    <text class="title">历史作品</text>
    <text class="subtitle">回看每次提交，持续观察自己的成长轨迹。</text>

    <view class="section history-list">
      <view v-for="item in studentStore.history" :key="item.id" class="card history-item" @tap="openResult(item.id)">
        <image class="thumb" :src="studentStore.absoluteUrl(item.image_url)" mode="aspectFill" />
        <view class="history-info">
          <text class="history-title">作品 #{{ item.id }}</text>
          <text class="history-meta">任务 {{ item.task_id }} · {{ item.status }}</text>
          <text class="history-date">{{ item.submitted_at || "刚刚提交" }}</text>
        </view>
      </view>
    </view>

    <view v-if="!studentStore.history.length" class="card section empty">
      <text>还没有历史作品，完成一次上传后会出现在这里。</text>
    </view>
  </view>
</template>

<style scoped>
.history-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  display: flex;
  gap: 20rpx;
  align-items: center;
}

.thumb {
  width: 132rpx;
  height: 132rpx;
  flex: 0 0 132rpx;
  border-radius: 14rpx;
  background: #f3f4f6;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #111827;
}

.history-meta,
.history-date {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.empty {
  font-size: 28rpx;
  color: #6b7280;
}
</style>
