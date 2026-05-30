<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useTeacherStore } from "../../stores/teacher";
import ReviewPanel from "../review/index.vue";

const store = useTeacherStore();
const { reviews, reviewLoading } = storeToRefs(store);
</script>

<template>
  <ReviewPanel :reviews="reviews" :loading="reviewLoading" />
</template>
