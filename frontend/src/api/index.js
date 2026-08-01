/**
 * API 请求层
 * 封装 axios，统一处理 Token 携带、错误提示等
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例，配置默认行为
const api = axios.create({
  baseURL: '/',        // Vite 代理会把 /api 转发到后端
  timeout: 60000,       // 60 秒超时（LLM 回答可能较慢）
})

// 请求拦截器：自动携带 JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => response.data,  // 直接返回 data 部分
  (error) => {
    const { response } = error
    if (response) {
      switch (response.status) {
        case 401:
          // Token 过期或无效，清除登录状态
          localStorage.removeItem('token')
          localStorage.removeItem('username')
          localStorage.removeItem('userRole')
          ElMessage.error('登录已过期，请重新登录')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1500)
          break
        case 403:
          ElMessage.error('没有权限访问此功能')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(response.data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default api
