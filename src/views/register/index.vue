<template>
  <div class="register-page">
    <div class="register-card">
      <div class="register-header">
        <h1>创建账号</h1>
        <p>注册你的 AI 知识库账号</p>
      </div>

      <a-form
        :model="form"
        :rules="rules"
        layout="vertical"
        @finish="handleRegister"
      >
        <a-form-item
          label="用户名"
          name="username"
        >
          <a-input
            v-model:value="form.username"
            placeholder="请输入用户名"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="邮箱"
          name="email"
        >
          <a-input
            v-model:value="form.email"
            placeholder="请输入邮箱"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="手机号"
          name="phone"
        >
          <a-input
            v-model:value="form.phone"
            placeholder="请输入手机号"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="密码"
          name="password"
        >
          <a-input-password
            v-model:value="form.password"
            placeholder="请输入密码"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="确认密码"
          name="confirmPassword"
        >
          <a-input-password
            v-model:value="form.confirmPassword"
            placeholder="请再次输入密码"
            size="large"
          />
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            注册
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-link">
        已经有账号？
        <span @click="goLogin">
          立即登录
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = async (
  _rule: any,
  value: string
) => {
  if (!value) {
    return Promise.reject(
      new Error('请确认密码')
    )
  }

  if (value !== form.password) {
    return Promise.reject(
      new Error('两次输入的密码不一致')
    )
  }

  return Promise.resolve()
}

const rules = {
  username: [
    {
      required: true,
      message: '请输入用户名',
    },
    {
      min: 3,
      max: 50,
      message: '用户名长度为 3-50 个字符',
    },
  ],

  email: [
    {
      required: true,
      message: '请输入邮箱',
    },
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
    },
  ],

  phone: [
    {
      required: true,
      message: '请输入手机号',
    },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号',
    },
  ],

  password: [
    {
      required: true,
      message: '请输入密码',
    },
    {
      min: 6,
      message: '密码至少 6 位',
    },
  ],

  confirmPassword: [
    {
      validator: validateConfirmPassword,
    },
  ],
}

const handleRegister = async () => {
  loading.value = true

  try {
    const response = await request.post(
      '/register',
      {
        username: form.username,
        email: form.email,
        phone: form.phone,
        password: form.password,
      }
    )

    message.success(
      response.data.message || '注册成功'
    )

    router.push('/login')
  } catch (error: any) {
    message.error(
      error.response?.data?.message ||
      '注册失败'
    )
  } finally {
    loading.value = false
  }
}

const goLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  padding: 24px;
}

.register-card {
  width: 420px;
  max-width: 100%;
  padding: 36px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
}

.register-header {
  margin-bottom: 28px;
  text-align: center;
}

.register-header h1 {
  margin-bottom: 8px;
  font-size: 28px;
  font-weight: 600;
}

.register-header p {
  margin: 0;
  color: #8c8c8c;
}

.login-link {
  margin-top: 8px;
  text-align: center;
  color: #8c8c8c;
}

.login-link span {
  margin-left: 4px;
  color: #1677ff;
  cursor: pointer;
}

.login-link span:hover {
  text-decoration: underline;
}
</style>