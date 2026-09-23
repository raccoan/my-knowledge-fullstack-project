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
      path: '/register',
      component: () => import('@/views/register/index.vue'),
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
      path:'/resume',
      name:'Resume',
      component:()=>import('@/views/resume/index.vue'),
      meta:{
        requiresAuth: true,
      },
    },
    {
      path:'/interview',
      name:'Interview',
      component:()=>import('@/views/interview/index.vue'),
      meta:{
        requiresAuth: true,
      },
    },

    {
      path: '/',
      redirect: '/chat'
    }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem("token")

  if (to.meta.requiresAuth && !token) {
    return '/login'
    
  }
  if (to.path === '/login' && token) {
    return '/chat'
    
  }
  return true
})

export default router