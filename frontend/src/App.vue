<script setup lang="ts">
/** 全站视觉 Token：不影响接口、状态或页面结构。 */
const theme = {
  token: {
    colorPrimary: '#5b5ce2',
    colorInfo: '#5b5ce2',
    colorSuccess: '#2f9b6f',
    colorWarning: '#d99032',
    colorText: '#20212b',
    colorTextSecondary: '#737583',
    colorBorder: '#e8e8ef',
    colorBgLayout: '#f7f7fb',
    borderRadius: 10,
    fontFamily: 'Inter, "PingFang SC", "Microsoft YaHei", sans-serif',
  },
  components: {
    Button: {
      controlHeight: 36,
      primaryShadow: '0 8px 18px rgb(91 92 226 / 18%)',
    },
    Card: {
      borderRadiusLG: 16,
    },
  },
}
</script>

<template>
  <a-config-provider :theme="theme">
    <!-- 【微交互】只为路由内容增加轻量过渡，不改变各页面原有结构。 -->
    <router-view v-slot="{ Component }">
      <transition
        name="app-route"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
  </a-config-provider>
</template>
