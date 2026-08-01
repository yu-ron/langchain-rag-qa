import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/Register.vue'),
      meta: { title: '注册' },
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/Chat.vue'),
      meta: { title: '智能问答', requiresAuth: true },
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('@/views/Knowledge.vue'),
      meta: { title: '知识库管理', requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/Profile.vue'),
      meta: { title: '个人中心', requiresAuth: true },
    },
  ],
})

// 路由守卫：检查登录状态和权限
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  // 设置页面标题
  document.title = to.meta.title
    ? `${to.meta.title} - RAG 知识库问答系统`
    : 'RAG 知识库问答系统'

  // 需要登录的页面，但用户没有 Token
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && userRole !== 'admin') {
    return next('/chat') // 普通用户跳转到问答页
  }

  // 已登录用户访问登录/注册页，直接跳转问答页
  if (token && (to.path === '/login' || to.path === '/register')) {
    return next('/chat')
  }

  next()
})

export default router
