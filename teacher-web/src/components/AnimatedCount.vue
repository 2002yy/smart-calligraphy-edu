<script setup lang="ts">
import { useCountUp } from "../composables/useCountUp";

const props = withDefaults(defineProps<{
  value: number;
  duration?: number;
}>(), { duration: 300 });

const display = useCountUp(() => props.value, props.duration);
</script>

<template>
  <strong>{{ display }}</strong>
</template>
