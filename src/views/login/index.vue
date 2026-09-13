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

<style scoped>
.login-page {
  min-height: 100vh;

  display: flex;
  align-items: center;
  justify-content: center;

  background:
    radial-gradient(
      circle at 20% 20%,
      #e6f4ff,
      transparent 35%
    ),
    #f5f7fa;
}

.login-card {
  width: 420px;
  padding: 42px;

  background: rgba(255, 255, 255, 0.95);

  border: 1px solid #e8e8e8;
  border-radius: 16px;

  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.08);
}

.logo {
  width: 48px;
  height: 48px;

  margin: 0 auto 18px;

  display: flex;
  align-items: center;
  justify-content: center;

  color: #fff;
  font-size: 18px;
  font-weight: 600;

  background: #1677ff;
  border-radius: 12px;
}

.login-card h1 {
  margin: 0;

  text-align: center;

  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  margin: 8px 0 32px;

  color: #999;
  text-align: center;
}
</style>