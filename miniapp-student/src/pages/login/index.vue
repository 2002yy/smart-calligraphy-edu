<script setup lang="ts">
import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();
</script>

<template>
  <view class="page login-page">
    <view class="brand-block">
      <view class="brand-mark">书</view>
      <text class="title">智慧书法学生端</text>
      <text class="subtitle">登录后查看练习任务，拍照上传作品，并获取 AI 评分建议。</text>
    </view>

    <view class="card login-card">
      <view class="field">
        <text class="label">账号</text>
        <input v-model="studentStore.username" class="input" placeholder="请输入学生账号" />
      </view>
      <view class="field">
        <text class="label">密码</text>
        <input v-model="studentStore.password" class="input" password placeholder="请输入密码" />
      </view>

      <button class="primary-button" :loading="studentStore.loading" @tap="studentStore.login">登录</button>
      <text class="hint">{{ studentStore.message }}</text>
    </view>
  </view>
</template>

<style scoped>
.login-page {
  padding-top: 120rpx;
}

.brand-block {
  margin-bottom: 48rpx;
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
