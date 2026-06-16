<script setup lang="ts">
import { onLaunch } from "@dcloudio/uni-app";

import { useStudentStore } from "./stores/student";

const studentStore = useStudentStore();

onLaunch(() => {
  studentStore.restoreSession();
});
</script>

<style>
page {
  min-height: 100%;
  background: #f7f8fb;
  color: #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

view,
text,
button,
input {
  box-sizing: border-box;
}

button {
  border: 0;
}

.page {
  min-height: 100vh;
  padding: 32rpx;
}

.section {
  margin-top: 28rpx;
}

.card {
  border-radius: 16rpx;
  background: #ffffff;
  padding: 28rpx;
  box-shadow: 0 12rpx 34rpx rgba(15, 23, 42, 0.06);
}

.title {
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.25;
  color: #111827;
}

.subtitle {
  margin-top: 12rpx;
  font-size: 26rpx;
  line-height: 1.6;
  color: #6b7280;
}

.primary-button {
  height: 88rpx;
  border-radius: 14rpx;
  background: #111827;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 88rpx;
}

.secondary-button {
  height: 80rpx;
  border-radius: 14rpx;
  background: #eef2ff;
  color: #3730a3;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 80rpx;
}

.muted {
  color: #6b7280;
}
</style>
