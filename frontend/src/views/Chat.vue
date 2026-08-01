<template>
  <AppLayout>
    <template #sidebar>
      <el-button type="primary" style="width: 100%; margin-bottom: 15px" @click="handleNewChat">
        <el-icon><Plus /></el-icon> 新对话
      </el-button>

      <div style="flex: 1; overflow-y: auto">
        <div
          v-for="session in sessionStore.sessions"
          :key="session.id"
          :style="{
            padding: '10px 12px',
            marginBottom: '4px',
            borderRadius: '8px',
            cursor: 'pointer',
            background: session.id === chatStore.currentSessionId ? '#ecf5ff' : 'transparent',
          }"
          @click="switchSession(session.id)"
        >
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span
              style="font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1"
            >
              {{ session.title }}
            </span>
            <el-dropdown trigger="click" @command="(cmd) => handleSessionAction(cmd, session)">
              <el-icon style="cursor: pointer"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <p style="font-size: 12px; color: #909399; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
            {{ session.preview || '点击开始对话' }}
          </p>
        </div>
      </div>
    </template>

    <template #main>
      <div style="padding: 15px 30px; background: #fff; border-bottom: 1px solid #e4e7ed">
        <span style="font-size: 16px; font-weight: 500">智能问答</span>
      </div>

      <div style="flex: 1; overflow-y: auto; padding: 20px 30px" ref="chatContainer">
        <div v-if="!chatStore.hasMessages" style="text-align: center; margin-top: 100px">
          <el-icon :size="60" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p style="color: #909399; margin-top: 20px; font-size: 16px">
            欢迎使用 RAG 知识库问答系统
          </p>
          <p style="color: #c0c4cc; font-size: 14px">
            上传知识库文档后，向我提问商品相关问题吧
          </p>
        </div>

        <div v-for="(msg, idx) in chatStore.messages" :key="idx" style="margin-bottom: 25px">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" style="display: flex; justify-content: flex-end">
            <div
              style="max-width: 70%; padding: 12px 18px; background: #409eff; color: #fff; border-radius: 12px 12px 4px 12px; line-height: 1.6; white-space: pre-wrap"
            >
              {{ msg.content }}
            </div>
          </div>

          <!-- AI 消息 -->
          <div v-else style="display: flex; gap: 12px">
            <el-avatar :size="36" style="background: #67c23a">
              <el-icon><Cpu /></el-icon>
            </el-avatar>
            <div style="flex: 1; max-width: 80%">
              <div
                style="padding: 12px 18px; background: #fff; border-radius: 4px 12px 12px 12px; line-height: 1.8; box-shadow: 0 1px 3px rgba(0,0,0,0.06); white-space: pre-wrap"
              >
                <!-- 渲染带引用标签的回答 -->
                <span v-html="renderContent(msg.content)"></span>

                <!-- 引用来源（可折叠） -->
                <div
                  v-if="msg.citations && msg.citations.length > 0"
                  style="margin-top: 12px"
                >
                  <el-button
                    text
                    size="small"
                    style="font-size: 12px; color: #909399"
                    @click="toggleCitations(idx)"
                  >
                    <el-icon style="margin-right: 4px">
                      <ArrowRight v-if="!showCitations[idx]" />
                      <ArrowDown v-else />
                    </el-icon>
                    引用来源 ({{ msg.citations.length }}条)
                  </el-button>
                  <div
                    v-show="showCitations[idx]"
                    style="margin-top: 8px; padding: 10px 12px; background: #f8f9fb; border-radius: 8px; border: 1px solid #ebeef5"
                  >
                    <div
                      v-for="(cite, ci) in msg.citations"
                      :key="ci"
                      style="padding: 6px 10px; margin-bottom: 4px; background: #fff; border-radius: 4px; font-size: 13px; color: #606266; border-left: 3px solid #409eff"
                    >
                      <strong>[来源{{ cite.index }}]</strong>
                      {{ (cite.content || '').substring(0, 200) }}{{ (cite.content || '').length > 200 ? '...' : '' }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 反馈按钮 -->
              <div style="margin-top: 6px; display: flex; gap: 10px" v-if="msg.content">
                <el-button
                  text size="small"
                  :type="msg.feedback === 'like' ? 'primary' : 'default'"
                  @click="handleFeedback(msg, 'like')"
                >
                  <el-icon><Select /></el-icon> 有用
                </el-button>
                <el-button
                  text size="small"
                  :type="msg.feedback === 'dislike' ? 'danger' : 'default'"
                  @click="handleFeedback(msg, 'dislike')"
                >
                  <el-icon><CloseBold /></el-icon> 没用
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="chatStore.loading" style="display: flex; gap: 12px; margin-bottom: 25px">
          <el-avatar :size="36" style="background: #67c23a">
            <el-icon><Cpu /></el-icon>
          </el-avatar>
          <div style="padding: 12px 18px; background: #fff; border-radius: 12px">
            <span class="dot-pulse"></span>
          </div>
        </div>
      </div>

      <div style="padding: 15px 30px; background: #fff; border-top: 1px solid #e4e7ed">
        <div style="display: flex; gap: 12px; align-items: flex-end">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入你的问题，例如：这款手机的电池续航怎么样？"
            resize="none"
            :disabled="chatStore.loading"
            @keyup.enter.exact="handleSend"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="chatStore.loading"
            @click="handleSend"
            :disabled="!inputText.trim() || chatStore.loading || !chatStore.currentSessionId"
            style="height: 42px"
          >
            发送
          </el-button>
        </div>
        <p style="font-size: 12px; color: #c0c4cc; margin-top: 6px">
          按 Enter 发送 | AI 回答基于知识库内容，引用来源可点击查看
        </p>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatDotRound, Cpu, Promotion, Select, CloseBold, MoreFilled, ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import { useChatStore } from '@/stores/chat'
import { useSessionStore } from '@/stores/session'

const chatStore = useChatStore()
const sessionStore = useSessionStore()

const inputText = ref('')
const chatContainer = ref(null)
const showCitations = ref({})  // 控制每条消息的引用来源折叠/展开

function toggleCitations(idx) {
  showCitations.value[idx] = !showCitations.value[idx]
}

// 初始化：加载会话列表，自动创建或选择第一个会话
onMounted(async () => {
  await sessionStore.fetchSessions()
  if (sessionStore.sessions.length > 0) {
    await switchSession(sessionStore.sessions[0].id)
  } else {
    await handleNewChat()
  }
})

// 切换会话
async function switchSession(sessionId) {
  await chatStore.loadMessages(sessionId)
  scrollToBottom()
}

// 新建对话
async function handleNewChat() {
  const newId = await sessionStore.createSession('新对话')
  chatStore.setSession(newId)
  chatStore.messages = []
  scrollToBottom()
}

// 发送消息
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading || !chatStore.currentSessionId) return
  inputText.value = ''
  await chatStore.sendMessage(chatStore.currentSessionId, text)
  scrollToBottom()
}

// 会话操作：重命名/删除
async function handleSessionAction(cmd, session) {
  if (cmd === 'rename') {
    try {
      const { value } = await ElMessageBox.prompt('请输入新名称', '重命名', {
        inputValue: session.title,
      })
      if (value) {
        await sessionStore.renameSession(session.id, value)
      }
    } catch { /* 用户取消 */ }
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('确定删除此会话？所有对话记录将被清除。', '确认删除', {
        type: 'warning',
      })
      await sessionStore.deleteSession(session.id)
      if (chatStore.currentSessionId === session.id) {
        chatStore.messages = []
        chatStore.currentSessionId = null
      }
      ElMessage.success('已删除')
    } catch { /* 用户取消 */ }
  }
}

// 消息反馈
async function handleFeedback(msg, type) {
  const newFeedback = msg.feedback === type ? null : type
  if (msg.id) {
    await chatStore.setFeedback(msg.id, newFeedback)
  }
  msg.feedback = newFeedback
}

// 把 [来源N] 渲染成可点击标签
function renderContent(text) {
  if (!text) return ''
  return text.replace(
    /\[来源(\d+)\]/g,
    '<span class="citation-tag">[$1]</span>'
  )
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, () => scrollToBottom())
</script>

<style scoped>
.dot-pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: pulse 1.4s infinite ease-in-out both;
}
@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}
</style>
