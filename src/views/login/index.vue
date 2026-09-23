<template>
  <div class="login-page">

    <div class="login-card">

      <div class="logo">
        AI
      </div>

      <h1>AI 知识库</h1>

      <p class="subtitle">
        基于 RAG 的智能知识库助手
      </p>

      <a-form
        :model="form"
        layout="vertical"
        @finish="handleLogin"
      >

        <a-form-item label="用户名">
          <a-input
            v-model:value="form.username"
            size="large"
            placeholder="请输入用户名"
          />
        </a-form-item>

        <a-form-item label="密码">
          <a-input-password
            v-model:value="form.password"
            size="large"
            placeholder="请输入密码"
          />
        </a-form-item>

        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="loading"
        >
          登录
        </a-button>

      </a-form>

    </div>

  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const handleLogin = async () => {
  if (!form.username.trim()) {
    message.warning('请输入用户名')
    return
  }

  if (!form.password) {
    message.warning('请输入密码')
    return
  }

  try {
    loading.value = true

    await userStore.login(
      form.username,
      form.password
    )

    message.success('登录成功')

    await router.push('/chat')

  } catch (error: any) {

    console.error('登录失败：', error)

    const errorMessage =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      '登录失败，请检查用户名和密码'

    message.error(errorMessage)

  } finally {
    loading.value = false
  }
}
</script>

```css
<style scoped>
.login-page {
  position: relative;

  min-height: 100vh;

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 24px;

  overflow: hidden;

  background:
    radial-gradient(
      circle at 15% 15%,
      rgb(22 119 255 / 10%),
      transparent 32%
    ),
    radial-gradient(
      circle at 85% 85%,
      rgb(91 110 225 / 7%),
      transparent 30%
    ),
    #f7f8fa;
}

/* =========================
   Login Card
========================= */

.login-card {
  position: relative;
  z-index: 1;

  width: min(420px, 100%);
  padding: 40px;

  background: rgb(255 255 255 / 96%);

  border: 1px solid #e8eaed;
  border-radius: 14px;

  box-shadow:
    0 12px 40px rgb(31 35 41 / 7%),
    0 2px 8px rgb(31 35 41 / 3%);

  backdrop-filter: blur(10px);
}

/* =========================
   Logo
========================= */

.logo {
  width: 48px;
  height: 48px;

  margin: 0 auto 18px;

  display: flex;
  align-items: center;
  justify-content: center;

  color: #ffffff;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;

  background: linear-gradient(
    135deg,
    #1677ff,
    #5b8ff9
  );

  border-radius: 12px;

  box-shadow:
    0 6px 16px rgb(22 119 255 / 20%),
    inset 0 1px 0 rgb(255 255 255 / 20%);
}

/* =========================
   Title
========================= */

.login-card h1 {
  margin: 0;

  color: #1f2329;

  text-align: center;

  font-size: 24px;
  line-height: 32px;
  font-weight: 600;
}

.subtitle {
  margin: 7px 0 30px;

  color: #86909c;

  text-align: center;

  font-size: 12px;
  line-height: 18px;
}

/* =========================
   Form
========================= */

.login-card :deep(.ant-form-item) {
  margin-bottom: 18px;
}

.login-card :deep(.ant-form-item-label) {
  padding-bottom: 6px;
}

.login-card :deep(.ant-form-item-label > label) {
  color: #4e5969;
  font-size: 12px;
  font-weight: 500;
}

/* =========================
   Input
========================= */

.login-card :deep(.ant-input),
.login-card :deep(.ant-input-affix-wrapper) {
  min-height: 42px;

  color: #1f2329;

  border-color: #d9dce1;
  border-radius: 8px;

  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.login-card :deep(.ant-input:hover),
.login-card :deep(.ant-input-affix-wrapper:hover) {
  border-color: #b8c7dc;
}

.login-card :deep(.ant-input:focus),
.login-card :deep(.ant-input-affix-wrapper-focused) {
  border-color: #91bfff;

  box-shadow:
    0 0 0 3px rgb(22 119 255 / 7%);
}

.login-card :deep(.ant-input::placeholder) {
  color: #b2b7c2;
}

.login-card :deep(.ant-input-password-icon) {
  color: #a9aeb8;
}

.login-card :deep(.ant-input-password-icon:hover) {
  color: #1677ff;
}

/* =========================
   Login Button
========================= */

.login-card :deep(.ant-btn-primary) {
  height: 42px;

  margin-top: 4px;

  border: none;
  border-radius: 8px;

  font-size: 13px;
  font-weight: 500;

  box-shadow:
    0 4px 10px rgb(22 119 255 / 16%);

  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease;
}

.login-card :deep(.ant-btn-primary:hover) {
  transform: translateY(-1px);

  box-shadow:
    0 6px 14px rgb(22 119 255 / 20%);
}

.login-card :deep(.ant-btn-primary:active) {
  transform: translateY(0);
}

/* =========================
   Mobile
========================= */

@media (max-width: 480px) {
  .login-page {
    padding: 16px;
  }

  .login-card {
    padding: 32px 24px;

    border-radius: 12px;
  }

  .login-card h1 {
    font-size: 22px;
  }

  .subtitle {
    margin-bottom: 26px;
  }
}
</style>
```
