<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import { useStudentStore } from "../../stores/student";

const studentStore = useStudentStore();
const previewPath = ref("");

onLoad((query) => {
  const id = Number(query?.id);
  if (id) {
    studentStore.loadTask(id);
  }
});

function chooseImage() {
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["camera", "album"],
    success: (res) => {
      previewPath.value = res.tempFilePaths[0] || "";
    }
  });
}

function submit() {
  if (!previewPath.value) {
    studentStore.setMessage("请先拍照或从相册选择一张作品。");
    return;
  }
  studentStore.submitAndEvaluate(previewPath.value);
}
</script>

<template>
  <view class="page">
    <text class="title">上传作品</text>
    <text class="subtitle">{{ studentStore.selectedTask?.title || "选择任务后上传作品" }}</text>

    <view class="card section upload-box" @tap="chooseImage">
      <image v-if="previewPath" class="preview" :src="previewPath" mode="aspectFit" />
      <view v-else class="placeholder">
        <text class="placeholder-title">拍照或选择图片</text>
        <text class="placeholder-desc">建议正对纸面，保持光线均匀，图片不超过 5MB。</text>
      </view>
    </view>

    <button class="secondary-button section" @tap="chooseImage">重新选择</button>
    <button class="primary-button section" :loading="studentStore.stage === 'uploading' || studentStore.stage === 'evaluating'" @tap="submit">
      {{ studentStore.stage === "evaluating" ? "AI 正在评分" : "提交并评分" }}
    </button>
    <text class="message">{{ studentStore.message }}</text>
  </view>
</template>

<style scoped>
.upload-box {
  min-height: 560rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview {
  width: 100%;
  height: 560rpx;
}

.placeholder {
  text-align: center;
}

.placeholder-title {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
  color: #111827;
}

.placeholder-desc {
  display: block;
  width: 480rpx;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.6;
  color: #6b7280;
}

.message {
  display: block;
  margin-top: 22rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: #6b7280;
}
</style>
