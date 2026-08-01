/**
 * 会话列表状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentId = ref(null)

  /** 获取会话列表 */
  async function fetchSessions() {
    try {
      const res = await api.get('/api/sessions', {
        params: { page: 1, page_size: 50 },
      })
      sessions.value = res.items || []
    } catch {
      sessions.value = []
    }
  }

  /** 创建新会话 */
  async function createSession(title = '新对话') {
    const res = await api.post('/api/sessions', { title })
    sessions.value.unshift({
      id: res.id,
      title: res.title,
      preview: '',
      created_at: res.created_at,
      updated_at: res.created_at,
    })
    return res.id
  }

  /** 重命名会话 */
  async function renameSession(sessionId, title) {
    await api.put(`/api/sessions/${sessionId}`, { title })
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session) session.title = title
  }

  /** 删除会话 */
  async function deleteSession(sessionId) {
    await api.delete(`/api/sessions/${sessionId}`)
    sessions.value = sessions.value.filter((s) => s.id !== sessionId)
  }

  return {
    sessions,
    currentId,
    fetchSessions,
    createSession,
    renameSession,
    deleteSession,
  }
})
