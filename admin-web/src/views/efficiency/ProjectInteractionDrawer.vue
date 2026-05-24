<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createProjectComment, deleteProjectComment, listProjectComments,
  type ProjectComment,
} from '@/api/projects'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  modelValue: boolean
  projectId: number | null
  projectName: string
}>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  refreshed: []
}>()

const auth = useAuthStore()

const comments = ref<ProjectComment[]>([])
const loading = ref(false)
const newBody = ref('')
const submitting = ref(false)

const ROLE_LABEL: Record<string, string> = {
  admin: '管理员', lead: '团队负责人', pm: 'PM',
  finance: '财务', engineer: '工程师', vendor: 'Vendor',
}
const ROLE_COLOR: Record<string, string> = {
  admin: 'danger', lead: 'danger', pm: 'warning',
  finance: 'info', engineer: 'success', vendor: 'info',
}

async function refresh() {
  if (!props.projectId) return
  loading.value = true
  try {
    comments.value = await listProjectComments(props.projectId)
  } finally {
    loading.value = false
  }
}

watch(() => [props.modelValue, props.projectId], ([open]) => {
  if (open && props.projectId) {
    newBody.value = ''
    refresh()
  }
})

async function onSubmit() {
  if (!props.projectId || !newBody.value.trim()) {
    ElMessage.warning('请输入留言内容')
    return
  }
  submitting.value = true
  try {
    await createProjectComment(props.projectId, newBody.value.trim())
    newBody.value = ''
    await refresh()
    emit('refreshed')
  } finally {
    submitting.value = false
  }
}

async function onDelete(c: ProjectComment) {
  await ElMessageBox.confirm('删除这条留言？', '提示', { type: 'warning' })
  if (!props.projectId) return
  await deleteProjectComment(props.projectId, c.id)
  await refresh()
  emit('refreshed')
}

function canDelete(c: ProjectComment) {
  return auth.role === 'admin' || auth.role === 'lead' || c.author_user_id === auth.userId
}

function timeAgo(iso: string) {
  const t = new Date(iso).getTime()
  const diff = Date.now() - t
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    direction="rtl" size="540px"
    :title="`${projectName || '项目'} · 互动留言`"
  >
    <div v-loading="loading">
      <div v-if="!comments.length" style="color: #909399; text-align: center; padding: 24px">
        暂无留言。管理员、PM、工程师可在此互相催办 / 回复 / 备注。
      </div>
      <div v-else>
        <div
          v-for="c in comments" :key="c.id"
          style="border-bottom: 1px solid #ebeef5; padding: 10px 0"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px">
            <div>
              <el-tag :type="(ROLE_COLOR[c.author_role] as any) || 'info'" size="small" effect="plain">
                {{ ROLE_LABEL[c.author_role] || c.author_role }}
              </el-tag>
              <span style="margin-left: 6px; font-weight: 600">{{ c.author_name || '—' }}</span>
              <span style="margin-left: 8px; color: #909399; font-size: 12px">{{ timeAgo(c.created_at) }}</span>
            </div>
            <el-button v-if="canDelete(c)" link type="danger" size="small" @click="onDelete(c)">删除</el-button>
          </div>
          <div style="white-space: pre-wrap; color: #303133">{{ c.body }}</div>
        </div>
      </div>

      <div style="margin-top: 16px; border-top: 2px solid #ebeef5; padding-top: 12px">
        <el-input
          v-model="newBody" type="textarea" :rows="3"
          placeholder="留言给项目相关方（admin/PM/工程师都能看到）"
          maxlength="2000" show-word-limit
        />
        <div style="text-align: right; margin-top: 8px">
          <el-button type="primary" :loading="submitting" @click="onSubmit">发送</el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>
