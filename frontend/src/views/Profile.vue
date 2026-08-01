<template>
  <AppLayout>
    <template #sidebar>
      <div style="padding: 10px 0">
        <p style="font-size: 13px; color: #909399; text-align: center">个人中心</p>
      </div>
    </template>

    <template #main>
      <div style="padding: 20px 30px; background: #fff; border-bottom: 1px solid #e4e7ed">
        <span style="font-size: 16px; font-weight: 500">个人中心</span>
      </div>

      <div style="flex: 1; padding: 40px; display: flex; justify-content: center">
        <div style="width: 500px">
          <!-- 用户信息卡片 -->
          <el-card style="margin-bottom: 20px">
            <template #header>
              <span>基本信息</span>
            </template>
            <div style="display: flex; align-items: center; gap: 20px">
              <el-avatar :size="60">
                {{ authStore.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div>
                <p style="font-size: 18px; font-weight: 500">
                  {{ authStore.username }}
                  <el-tag
                    :type="authStore.isAdmin ? 'danger' : 'info'"
                    size="small"
                    style="margin-left: 8px"
                  >
                    {{ authStore.isAdmin ? '管理员' : '普通用户' }}
                  </el-tag>
                </p>
                <p style="color: #909399; font-size: 13px; margin-top: 4px">
                  用户ID: {{ authStore.userId }}
                </p>
              </div>
            </div>
          </el-card>

          <!-- 修改密码 -->
          <el-card>
            <template #header>
              <span>修改密码</span>
            </template>
            <el-form
              :model="passwordForm"
              :rules="passwordRules"
              ref="passwordFormRef"
              label-width="80px"
            >
              <el-form-item label="旧密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  show-password
                  placeholder="请输入旧密码"
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  show-password
                  placeholder="请输入新密码（最少6位）"
                />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="请再次输入新密码"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="changing"
                  @click="handleChangePassword"
                >
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'

const authStore = useAuthStore()

const passwordFormRef = ref(null)
const changing = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const validateConfirm = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码最少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  changing.value = true
  try {
    await authStore.changePassword(
      passwordForm.oldPassword,
      passwordForm.newPassword
    )
    ElMessage.success('密码修改成功！')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch {
    // 错误已在 API 拦截器中处理
  } finally {
    changing.value = false
  }
}
</script>
