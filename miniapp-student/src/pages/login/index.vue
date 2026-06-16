<script setup lang="ts">
import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();
</script>

<template>
  <view class="page login-page">
    <view class="brand-block">
      <view class="brand-mark">S</view>
      <text class="title">Smart Calligraphy</text>
      <text class="subtitle">Student miniapp test build. Use the demo account below to verify login, tasks, upload, and AI result.</text>
    </view>

    <view class="card demo-card">
      <text class="demo-title">Test build info</text>
      <text class="demo-line">Account: student01</text>
      <text class="demo-line">Password: 123456</text>
      <text class="demo-line">Invite code: CALLI2026</text>
      <button class="secondary-button demo-button" @tap="studentStore.fillDemoAccount">Fill demo info</button>
    </view>

    <view class="card login-card">
      <view class="field">
        <text class="label">Account</text>
        <input v-model="studentStore.username" class="input" placeholder="student01" />
      </view>
      <view class="field">
        <text class="label">Password</text>
        <input v-model="studentStore.password" class="input" password placeholder="123456" />
      </view>

      <button class="primary-button" :loading="studentStore.loading" @tap="studentStore.login">Login</button>
      <text class="hint">{{ studentStore.message }}</text>
    </view>
  </view>
</template>

<style scoped>
.login-page {
  padding-top: 80rpx;
}

.brand-block {
  margin-bottom: 28rpx;
}

.brand-mark {
  width: 96rpx;
  height: 96rpx;
  margin-bottom: 28rpx;
  border-radius: 24rpx;
  background: #111827;
  color: #ffffff;
  font-size: 48rpx;
  font-weight: 800;
  line-height: 96rpx;
  text-align: center;
}

.demo-card {
  margin-bottom: 24rpx;
  background: #eef2ff;
  box-shadow: none;
}

.demo-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #3730a3;
}

.demo-line {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  color: #312e81;
}

.demo-button {
  margin-top: 20rpx;
}

.login-card {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.label {
  font-size: 26rpx;
  font-weight: 700;
  color: #374151;
}

.input {
  height: 88rpx;
  border-radius: 14rpx;
  background: #f3f4f6;
  padding: 0 24rpx;
  font-size: 30rpx;
}

.hint {
  font-size: 24rpx;
  line-height: 1.5;
  color: #6b7280;
}
</style>
