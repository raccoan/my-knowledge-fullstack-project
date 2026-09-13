import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/index.vue')
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/chat/index.vue'),
      meta: {
        requiresAuth: true
      },
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('../views/knowledge/index.vue'),
      meta: {
        requiresAuth: true
      },
    },

    {
      path: '/',
      redirect: '/chat'
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("token")

  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  if (to.path === '/login' && token) {
    next('/chat')
    return
  }
  next()
})

export default router