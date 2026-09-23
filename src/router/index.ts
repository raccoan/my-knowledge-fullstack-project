import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () =>
        import('../views/login/index.vue')
    },

    {
      path: '/register',
      name: 'Register',
      component: () =>
        import('@/views/register/index.vue')
    },

    {
      path: '/chat',
      name: 'Chat',
      component: () =>
        import('../views/chat/index.vue'),
      meta: {
        requiresAuth: true
      }
    },

    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () =>
        import('../views/knowledge/index.vue'),
      meta: {
        requiresAuth: true
      }
    },

    {
      path: '/resume',
      name: 'Resume',
      component: () =>
        import('@/views/resume/index.vue'),
      meta: {
        requiresAuth: true
      }
    },

    {
      path: '/interview',
      name: 'Interview',
      component: () =>
        import('@/views/interview/index.vue'),
      meta: {
        requiresAuth: true
      }
    },

    {
      path: '/',
      redirect: '/chat'
    }
  ]
})

router.beforeEach((to) => {
  const token =
    localStorage.getItem('token')

  // 需要登录，但没有 Token
  if (
    to.meta.requiresAuth &&
    !token
  ) {
    return '/login'
  }

  // 已经登录，不允许再进入登录/注册页面
  if (
    token &&
    (
      to.path === '/login' ||
      to.path === '/register'
    )
  ) {
    return '/chat'
  }

  return true
})

export default router