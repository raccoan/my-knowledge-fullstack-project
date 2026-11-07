<script setup lang="ts">
defineProps<{ seconds: number; reason: string }>()
</script>

<template>
  <a-alert v-if="seconds > 0" type="warning" show-icon role="status" class="request-cooldown"
    :message="`${reason}，${seconds} 秒后可重试。`" description="输入内容已保留，不会自动重新提交。" />
</template>

<style scoped>
.request-cooldown{margin:12px 0}
</style>
