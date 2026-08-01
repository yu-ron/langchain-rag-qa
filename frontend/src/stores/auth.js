/**
 * 用户认证状态管理
 * 管理登录状态、用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // ── 状态 ──
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const userRole = ref(localStorage.getItem('userRole') || '')
  const userId = ref(parseInt(localStorage.getItem('userId') || '0'))

  // ── 计算属性 ──
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userRole.value === 'admin')

  // ── 方法 ──

  /** 登录 */
  async function login(usernameVal, password) {
    const res = await api.post('/api/auth/login', {
      username: usernameVal,
      password,
    })
    saveLoginState(res)
    return res
  }

  /** 注册 */
  async function register(usernameVal, password) {
    return await api.post('/api/auth/register', {
      username: usernameVal,
      password,
    })
  }

  /** 获取当前用户信息 */
  async function fetchUserInfo() {
    const res = await api.get('/api/auth/me')
    userRole.value = res.role
    localStorage.setItem('userRole', res.role)
    return res
  }

  /** 修改密码 */
  async function changePassword(oldPassword, newPassword) {
    return await api.post('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  /** 保存登录状态到 localStorage */
  function saveLoginState(res) {
    token.value = res.token
    username.value = res.username
    userRole.value = res.role
    userId.value = res.user_id

    localStorage.setItem('token', res.token)
    localStorage.setItem('username', res.username)
    localStorage.setItem('userRole', res.role)
    localStorage.setItem('userId', res.user_id)
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    username.value = ''
    userRole.value = ''
    userId.value = 0

    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
    localStorage.removeItem('userId')
  }

  return {
    token,
    username,
    userRole,
    userId,
    isLoggedIn,
    isAdmin,
    login,
    register,
    fetchUserInfo,
    changePassword,
    logout,
  }
})
