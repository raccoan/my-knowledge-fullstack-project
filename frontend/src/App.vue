<script setup lang="ts">
</script>

<template>
  <!-- 【微交互】只为路由内容增加轻量过渡，不改变各页面原有结构。 -->
  <router-view v-slot="{ Component }">
    <transition
      name="app-route"
      mode="out-in"
    >
      <component :is="Component" />
    </transition>
  </router-view>
</template>
