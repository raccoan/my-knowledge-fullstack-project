<template>
  <div class="register-page">
    <div class="register-card">
      <div class="title">创建账号</div>
      <div class="subtitle">注册你的知识库账号</div>

      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        layout="vertical"
        @finish="handleRegister"
      >
        <!-- 用户名 -->
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

        <!-- 注册方式 -->
        <div class="register-type">
          <a-button
            :type="form.codeType === 'email' ? 'primary' : 'default'"
            @click="changeCodeType('email')"
          >
            邮箱注册
          </a-button>

          <a-button
            :type="form.codeType === 'phone' ? 'primary' : 'default'"
            @click="changeCodeType('phone')"
          >
            手机号注册
          </a-button>
        </div>

        <!-- 邮箱 -->
        <a-form-item
          v-if="form.codeType === 'email'"
          label="邮箱"
          name="email"
        >
          <a-input
            v-model:value="form.email"
            placeholder="请输入邮箱"
            size="large"
          />
        </a-form-item>

        <!-- 手机号 -->
        <a-form-item
          v-else
          label="手机号"
          name="phone"
        >
          <a-input
            v-model:value="form.phone"
            placeholder="请输入手机号"
            size="large"
          />
        </a-form-item>

        <!-- 验证码 -->
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

        <!-- 密码 -->
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

        <!-- 确认密码 -->
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

        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="registering"
        >
          注册
        </a-button>
      </a-form>

      <div class="login-link">
        已有账号？
        <span @click="router.push('/login')">
          返回登录
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

const formRef = ref()

const registering = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)

let timer: number | undefined

const form = reactive({
  username: '',
  email: '',
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
  codeType: 'email'
})

const validateConfirmPassword = async (
  _rule: Rule,
  value: string
) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }

  if (value !== form.password) {
    return Promise.reject('两次输入的密码不一致')
  }

  return Promise.resolve()
}

const rules = {
  username: [
    {
      required: true,
      message: '请输入用户名'
    },
    {
      min: 3,
      max: 50,
      message: '用户名长度为3-50个字符'
    }
  ],

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

  phone: [
    {
      required: true,
      message: '请输入手机号'
    },
    {
      pattern: /^1\d{10}$/,
      message: '请输入正确的手机号'
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
      message: '请输入密码'
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

function changeCodeType(
  type: 'email' | 'phone'
) {
  form.codeType = type
  form.code = ''

  if (type === 'email') {
    form.phone = ''
  } else {
    form.email = ''
  }

  formRef.value?.clearValidate([
    'email',
    'phone',
    'code'
  ])
}

async function sendCode() {
  const target =
    form.codeType === 'email'
      ? form.email
      : form.phone

  if (!target) {
    message.warning(
      form.codeType === 'email'
        ? '请输入邮箱'
        : '请输入手机号'
    )
    return
  }

  if (
    form.codeType === 'email' &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(target)
  ) {
    message.warning('请输入正确的邮箱地址')
    return
  }

  if (
    form.codeType === 'phone' &&
    !/^1\d{10}$/.test(target)
  ) {
    message.warning('请输入正确的手机号')
    return
  }

  try {
    sendingCode.value = true

    await request.post('/send-code', null, {
      params: {
        target,
        code_type: form.codeType
      }
    })

    message.success(
      '验证码发送成功，请查看后端控制台'
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
      '验证码发送失败'
    )
  } finally {
    sendingCode.value = false
  }
}

async function handleRegister() {
  try {
    registering.value = true

    const response = await request.post(
      '/register',
      {
        username: form.username,
        email:
          form.codeType === 'email'
            ? form.email
            : null,
        phone:
          form.codeType === 'phone'
            ? form.phone
            : null,
        code: form.code,
        code_type: form.codeType,
        password: form.password
      }
    )

    message.success(
      response.data.message || '注册成功'
    )
    router.push({
      path:'/login',
      query:{
        username:form.username
      }
    })

    router.push('/login')

  } catch (error: any) {
    console.log('注册失败:', error)
    console.log('后端返回:', error.response?.data)

    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      '注册失败，请稍后重试'

    message.error(errorMessage)

  } finally {
    registering.value = false
  }
}


</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
  padding: 20px;
}

.register-card {
  width: 420px;
  padding: 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.title {
  text-align: center;
  font-size: 26px;
  font-weight: 600;
  color: #1f2329;
}

.subtitle {
  margin-top: 8px;
  margin-bottom: 28px;
  text-align: center;
  color: #86909c;
  font-size: 14px;
}

.register-type {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}

.register-type .ant-btn {
  flex: 1;
}

.code-row {
  display: flex;
  gap: 10px;
}

.code-row .ant-input {
  flex: 1;
}

.code-row .ant-btn {
  flex-shrink: 0;
  width: 125px;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  color: #86909c;
  font-size: 14px;
}

.login-link span {
  margin-left: 4px;
  color: #1677ff;
  cursor: pointer;
}

.login-link span:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .register-card {
    width: 100%;
    padding: 28px 20px;
  }

  .code-row .ant-btn {
    width: 110px;
  }
}
</style>