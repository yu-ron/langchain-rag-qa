<template>
  <AppLayout>
    <template #sidebar>
      <div style="padding: 10px 0">
        <p style="font-size: 14px; font-weight: 500; text-align: center; margin-bottom: 10px">
          管理员操作面板
        </p>
        <el-divider />
        <div style="padding: 0 12px; font-size: 13px; color: #606266">
          <p>文档总数：{{ stats.document_count || 0 }}</p>
          <p>已完成：{{ stats.completed || 0 }}</p>
          <p>处理中：{{ stats.processing || 0 }}</p>
          <p>失败：{{ stats.failed || 0 }}</p>
        </div>
      </div>
    </template>

    <template #main>
      <div style="padding: 15px 30px; background: #fff; border-bottom: 1px solid #e4e7ed; display: flex; justify-content: space-between; align-items: center">
        <span>
          <span style="font-size: 16px; font-weight: 500">知识库管理</span>
          <el-tag type="danger" size="small" style="margin-left: 10px">管理员</el-tag>
        </span>
        <el-upload
          :http-request="handleUpload"
          :show-file-list="false"
          accept=".pdf,.txt,.csv,.md,.markdown,.docx,.doc"
          :before-upload="beforeUpload"
        >
          <el-button type="primary" :icon="Upload" :loading="uploading">
            上传文档
          </el-button>
        </el-upload>
      </div>

      <div style="flex: 1; padding: 20px 30px; overflow-y: auto">
        <!-- 搜索和统计 -->
        <div style="display: flex; justify-content: space-between; margin-bottom: 15px">
          <el-input
            v-model="search"
            placeholder="搜索文件名..."
            :prefix-icon="Search"
            style="width: 300px"
            clearable
            @change="loadDocuments"
          />
          <el-button @click="loadStats" :icon="RefreshRight">刷新</el-button>
        </div>

        <!-- 文档列表 -->
        <el-table :data="documents" style="width: 100%" v-loading="loading">
          <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="file_type" label="类型" width="80" />
          <el-table-column label="大小" width="100">
            <template #default="{ row }">
              {{ formatSize(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="row.status === 'processing'" type="warning" size="small">处理中</el-tag>
              <el-tooltip v-else-if="row.status === 'failed'" :content="row.error_message" placement="top">
                <el-tag type="danger" size="small">失败</el-tag>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="片段数" width="80" />
          <el-table-column label="上传时间" width="170">
            <template #default="{ row }">
              {{ row.created_at ? row.created_at.substring(0, 19) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button text type="danger" size="small" @click="handleDelete(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div style="display: flex; justify-content: center; margin-top: 20px">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="loadDocuments"
          />
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search, RefreshRight } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import api from '@/api'

const loading = ref(false)
const uploading = ref(false)
const documents = ref([])
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stats = ref({})

onMounted(() => {
  loadDocuments()
  loadStats()
})

async function loadDocuments() {
  loading.value = true
  try {
    const res = await api.get('/api/knowledge/documents', {
      params: { page: page.value, page_size: pageSize.value, search: search.value },
    })
    documents.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await api.get('/api/knowledge/stats')
  } catch { /* ignore */ }
}

function beforeUpload(file) {
  const allowed = ['.pdf', '.txt', '.csv', '.md', '.markdown', '.docx', '.doc']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowed.includes(ext)) {
    ElMessage.error(`不支持的文件类型: ${ext}`)
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

async function handleUpload({ file }) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await api.post('/api/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传成功，正在后台处理...')
    loadDocuments()
    loadStats()
  } catch { /* error handled by interceptor */ }
  finally {
    uploading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.filename}"？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await api.delete(`/api/knowledge/documents/${row.id}`)
    ElMessage.success('删除成功')
    loadDocuments()
    loadStats()
  } catch { /* error handled by interceptor */ }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}
</script>
