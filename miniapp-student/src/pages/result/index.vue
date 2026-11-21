<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();

onLoad((query) => {
  const id = Number(query?.id);
  if (id) {
    studentStore.loadResult(id);
  }
});

function goHistory() {
  uni.switchTab({ url: "/pages/history/index" });
}
</script>

<template>
  <view class="page">
    <view v-if="studentStore.latestResult" class="result">
      <view class="score-card">
        <text class="score">{{ studentStore.latestResult.score }}</text>
        <text class="level">{{ studentStore.latestResult.level }}</text>
        <text class="summary">{{ studentStore.latestResult.summary }}</text>
      </view>

      <image v-if="studentStore.resultImage" class="result-image section" :src="studentStore.resultImage" mode="aspectFit" />

      <view class="card section">
        <text class="block-title">评分细项</text>
        <view v-for="item in studentStore.latestResult.details" :key="item.name" class="detail-row">
          <view>
            <text class="detail-name">{{ item.name }}</text>
            <text class="detail-comment">{{ item.comment }}</text>
          </view>
          <text class="detail-score">{{ item.score }}</text>
        </view>
      </view>

      <button class="primary-button section" @tap="goHistory">查看历史作品</button>
    </view>
  </view>
</template>

<style scoped>
.score-card {
  border-radius: 20rpx;
  background: #111827;
  padding: 40rpx 32rpx;
  color: #ffffff;
}

.score {
  display: block;
  font-size: 88rpx;
  font-weight: 900;
  line-height: 1;
}

.level {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  font-weight: 800;
}

.summary {
  display: block;
  margin-top: 18rpx;
  font-size: 26rpx;
  line-height: 1.6;
  color: #d1d5db;
}

.result-image {
  width: 100%;
  height: 520rpx;
  border-radius: 16rpx;
  background: #ffffff;
}

.block-title {
  display: block;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #edf0f4;
}

.detail-row:last-child {
  border-bottom: 0;
}

.detail-name {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
}

.detail-comment {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: #6b7280;
}

.detail-score {
  font-size: 34rpx;
  font-weight: 900;
}
</style>
