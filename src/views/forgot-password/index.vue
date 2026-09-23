<template>
  <div class="forgot-page">
    <div class="forgot-card">
      <div class="title">找回密码</div>

      <div class="subtitle">
        通过注册邮箱重置密码
      </div>

      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        layout="vertical"
        @finish="handleResetPassword"
      >
        <a-form-item
          label="邮箱"
          name="email"
        >
          <a-input
            v-model:value="form.email"
            placeholder="请输入注册邮箱"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="验证码"
          name="code"
        >
          <div class="code-row">
            <a-input
              v-model:value="form.code"
              placeholder="请输入验证码"
              size="large"
            />

            <a-button
              size="large"
              :loading="sendingCode"
              :disabled="countdown > 0"
              @click="sendCode"
            >
              {{
                countdown > 0
                  ? `${countdown}s后重新获取`
                  : '获取验证码'
              }}
            </a-button>
          </div>
        </a-form-item>

        <a-form-item
          label="新密码"
          name="password"
        >
          <a-input-password
            v-model:value="form.password"
            placeholder="请输入新密码"
            size="large"
          />
        </a-form-item>

        <a-form-item
          label="确认新密码"
          name="confirmPassword"
        >
          <a-input-password
            v-model:value="form.confirmPassword"
            placeholder="请再次输入新密码"
            size="large"
          />
        </a-form-item>

        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="resetting"
        >
          重置密码
        </a-button>
      </a-form>

      <div class="login-link">
        想起密码了？
        <span @click="router.push('/login')">
          返回登录
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const formRef = ref()

const sendingCode = ref(false)
const resetting = ref(false)
const countdown = ref(0)

let timer: number | undefined

const form = reactive({
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = async (
  _rule: Rule,
  value: string
) => {
  if (!value) {
    return Promise.reject('请确认新密码')
  }

  if (value !== form.password) {
    return Promise.reject(
      '两次输入的密码不一致'
    )
  }

  return Promise.resolve()
}

const rules = {
  email: [
    {
      required: true,
      message: '请输入邮箱'
    },
    {
      type: 'email',
      message: '请输入正确的邮箱地址'
    }
  ],

  code: [
    {
      required: true,
      message: '请输入验证码'
    }
  ],

  password: [
    {
      required: true,
      message: '请输入新密码'
    },
    {
      min: 6,
      max: 100,
      message: '密码长度为6-100个字符'
    }
  ],

  confirmPassword: [
    {
      validator: validateConfirmPassword
    }
  ]
}

async function sendCode() {
  if (!form.email) {
    message.warning('请输入注册邮箱')
    return
  }

  if (
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
      form.email
    )
  ) {
    message.warning('请输入正确的邮箱地址')
    return
  }

  try {
    sendingCode.value = true

    await request.post(
      '/send-reset-code',
      null,
      {
        params: {
          email: form.email
        }
      }
    )

    message.success(
      '验证码发送成功，请查看邮箱'
    )

    countdown.value = 60

    timer = window.setInterval(() => {
      countdown.value--

      if (countdown.value <= 0) {
        if (timer) {
          clearInterval(timer)
        }

        timer = undefined
      }
    }, 1000)

  } catch (error: any) {
    message.error(
      error.response?.data?.detail ||
      '验证码发送失败，请稍后重试'
    )
  } finally {
    sendingCode.value = false
  }
}

async function handleResetPassword() {
  try {
    resetting.value = true

    const response = await request.post(
      '/reset-password',
      {
        email: form.email,
        code: form.code,
        password: form.password
      }
    )

    message.success(
      response.data.message ||
      '密码修改成功'
    )

    setTimeout(() => {
      router.push('/login')
    }, 800)

  } catch (error: any) {
    message.error(
      error.response?.data?.detail ||
      '密码修改失败，请稍后重试'
    )
  } finally {
    resetting.value = false
  }
}

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fb;
  padding: 24px;
}

.forgot-card {
  width: 420px;
  max-width: 100%;
  padding: 36px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.title {
  font-size: 26px;
  font-weight: 600;
  text-align: center;
  color: #1f2329;
}

.subtitle {
  margin-top: 8px;
  margin-bottom: 28px;
  text-align: center;
  color: #86909c;
}

.code-row {
  display: flex;
  gap: 12px;
}

.code-row .ant-input {
  flex: 1;
}

.code-row .ant-btn {
  flex-shrink: 0;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  color: #86909c;
}

.login-link span {
  color: #1677ff;
  cursor: pointer;
}

@media (max-width: 480px) {
  .forgot-card {
    padding: 28px 20px;
  }

  .code-row {
    gap: 8px;
  }

  .code-row .ant-btn {
    padding: 0 12px;
  }
}
</style>