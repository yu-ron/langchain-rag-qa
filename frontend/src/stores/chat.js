/**
 * 聊天状态管理
 * 管理消息列表、发送消息、接收流式回答
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])        // 当前会话的消息列表
  const currentSessionId = ref(null)  // 当前活跃的会话ID
  const loading = ref(false)      // 是否正在等待AI回答

  const hasMessages = computed(() => messages.value.length > 0)

  /** 设置当前会话 */
  function setSession(sessionId) {
    currentSessionId.value = sessionId
  }

  /** 加载会话的历史消息 */
  async function loadMessages(sessionId) {
    try {
      const res = await api.get(`/api/sessions/${sessionId}`)
      messages.value = res.messages || []
      currentSessionId.value = sessionId
    } catch {
      messages.value = []
    }
  }

  /** 发送消息并接收流式回答 */
  async function sendMessage(sessionId, question) {
    if (!question.trim() || loading.value) return

    // 添加用户消息
    messages.value.push({ role: 'user', content: question })
    loading.value = true

    // 准备 AI 消息占位
    const aiMsgIndex = messages.value.length
    messages.value.push({ role: 'assistant', content: '', citations: [], feedback: null })

    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: sessionId, question }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || '请求失败')
      }

      // 读取 SSE 流
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'content') {
                // 追加回答文字
                messages.value[aiMsgIndex].content += data.data
              } else if (data.type === 'citations') {
                // 设置引用来源
                messages.value[aiMsgIndex].citations = data.data
              } else if (data.type === 'error') {
                ElMessage.error(data.data)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (e) {
      messages.value[aiMsgIndex].content = '抱歉，请求失败：' + e.message
    } finally {
      loading.value = false
    }
  }

  /** 更新消息反馈 */
  async function setFeedback(messageId, feedback) {
    try {
      await api.post('/api/chat/feedback', {
        message_id: messageId,
        feedback,
      })
    } catch {
      // 静默失败
    }
  }

  return {
    messages,
    currentSessionId,
    loading,
    hasMessages,
    setSession,
    loadMessages,
    sendMessage,
    setFeedback,
  }
})
