<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h3>🤖 RAG 知识库问答</h3>
      </div>

      <!-- 会话列表（后续阶段实现） -->
      <div style="flex: 1; padding: 15px; overflow-y: auto">
        <slot name="sidebar" />
      </div>

      <!-- 底部用户信息 -->
      <div style="padding: 15px; border-top: 1px solid #e4e7ed">
        <el-dropdown trigger="click" style="width: 100%">
          <div style="display: flex; align-items: center; cursor: pointer; padding: 8px">
            <el-avatar :size="32" style="margin-right: 10px">
              {{ authStore.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div style="flex: 1">
              <div style="font-size: 14px; font-weight: 500">{{ authStore.username }}</div>
              <div style="font-size: 12px; color: #909399">
                {{ authStore.isAdmin ? '管理员' : '普通用户' }}
              </div>
            </div>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/chat')">
                <el-icon><ChatDotRound /></el-icon> 会话
              </el-dropdown-item>
              <el-dropdown-item @click="$router.push('/profile')">
                <el-icon><User /></el-icon> 个人中心
              </el-dropdown-item>
              <el-dropdown-item
                v-if="authStore.isAdmin"
                @click="$router.push('/knowledge')"
              >
                <el-icon><FolderOpened /></el-icon> 知识库管理
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <slot name="main" />
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
