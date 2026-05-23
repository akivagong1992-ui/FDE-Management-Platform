<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  APPROVAL_LABEL, APPROVAL_TAG_TYPE,
  acceptAssignment, addMessage, listAssignments, listMessages, rejectAssignment,
  type ApprovalStatus, type Assignment, type AssignmentMessage, type MessageKind,
} from '@/api/assignments'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ modelValue: boolean; assignmentId: number | null }>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  'changed': []
}>()

const auth = useAuthStore()
const isEngineerSide = computed(() => auth.role === 'engineer')
const canActPending = computed(() =>
  isEngineerSide.value
  && assignment.value?.approval_status === 'pending'
  && assignment.value?.engineer_id === auth.engineerId,
)

const assignment = ref<Assignment | null>(null)
const messages = ref<AssignmentMessage[]>([])
const loading = ref(false)
const reply = ref('')
const sending = ref(false)
const threadRef = ref<HTMLDivElement | null>(null)

async function load() {
  if (!props.assignmentId) return
  loading.value = true
  try {
    const [list, msgs] = await Promise.all([
      listAssignments(),
      listMessages(props.assignmentId),
    ])
    assignment.value = list.find((a) => a.id === props.assignmentId) ?? null
    messages.value = msgs
    await nextTick()
    threadRef.value?.scrollTo({ top: threadRef.value.scrollHeight })
  } finally {
    loading.value = false
  }
}

watch(() => [props.modelValue, props.assignmentId], ([open]) => {
  if (open && props.assignmentId) {
    reply.value = ''
    load()
  }
})

async function onSend() {
  const body = reply.value.trim()
  if (!body || !props.assignmentId) return
  sending.value = true
  try {
    const m = await addMessage(props.assignmentId, body)
    messages.value.push(m)
    reply.value = ''
    if (assignment.value) assignment.value.message_count += 1
    emit('changed')
    await nextTick()
    threadRef.value?.scrollTo({ top: threadRef.value.scrollHeight })
  } finally {
    sending.value = false
  }
}

const acceptNote = ref('')
async function onAccept() {
  if (!props.assignmentId) return
  sending.value = true
  try {
    await acceptAssignment(props.assignmentId, acceptNote.value || undefined)
    ElMessage.success('已接单')
    acceptNote.value = ''
    emit('changed')
    await load()
  } finally {
    sending.value = false
  }
}

const rejectVisible = ref(false)
const rejectReason = ref('')
async function onReject() {
  if (!rejectReason.value.trim() || !props.assignmentId) {
    ElMessage.warning('拒单理由必填')
    return
  }
  sending.value = true
  try {
    await rejectAssignment(props.assignmentId, rejectReason.value.trim())
    ElMessage.success('已拒单')
    rejectVisible.value = false
    rejectReason.value = ''
    emit('changed')
    await load()
  } finally {
    sending.value = false
  }
}

const SENDER_LABEL: Record<MessageKind, string> = {
  system: '系统', pm: '管理者', engineer: '工程师',
}
function formatTime(s: string): string {
  return s.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    direction="rtl" size="540px"
    :title="assignment ? `派单 #${assignment.id} · ${assignment.project_name}` : '加载中…'"
  >
    <div v-loading="loading" v-if="assignment">
      <!-- 元数据 -->
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="工程师">{{ assignment.engineer_name }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ assignment.role || '—' }}</el-descriptions-item>
        <el-descriptions-item label="计划起">{{ assignment.planned_start_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="计划止">{{ assignment.planned_end_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="工程师确认" :span="2">
          <el-tag :type="APPROVAL_TAG_TYPE[assignment.approval_status as ApprovalStatus]" size="small">
            {{ APPROVAL_LABEL[assignment.approval_status as ApprovalStatus] }}
          </el-tag>
          <span v-if="assignment.engineer_responded_at" style="margin-left: 8px; color: #909399; font-size: 12px">
            {{ formatTime(assignment.engineer_responded_at) }}
          </span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 对话线程 -->
      <div style="font-weight: 600; margin: 16px 0 8px">对话 ({{ messages.length }})</div>
      <div ref="threadRef" class="thread">
        <div v-if="messages.length === 0" class="empty">暂无消息</div>
        <div v-for="m in messages" :key="m.id"
             :class="['msg', `msg-${m.sender_kind}`]">
          <div class="msg-hdr">
            <span class="msg-from">{{ SENDER_LABEL[m.sender_kind] }}<span v-if="m.sender_name"> · {{ m.sender_name }}</span></span>
            <span class="msg-time">{{ formatTime(m.created_at) }}</span>
          </div>
          <div class="msg-body">{{ m.body }}</div>
        </div>
      </div>

      <!-- 工程师待确认时的接 / 拒按钮 -->
      <div v-if="canActPending" class="action-zone">
        <div style="font-weight: 600; margin-bottom: 6px">⚠️ 你的确认</div>
        <el-input v-model="acceptNote" placeholder="接单附言（可选）" style="margin-bottom: 6px" />
        <div style="display: flex; gap: 8px">
          <el-button type="success" :loading="sending" @click="onAccept">✓ 接单</el-button>
          <el-button type="danger" :loading="sending" @click="rejectVisible = true">✗ 拒单</el-button>
        </div>
      </div>

      <!-- 回复框（PM 永远可发；工程师在 accepted 后用于沟通后续）-->
      <div class="reply-zone" v-if="!canActPending">
        <el-input
          v-model="reply" type="textarea" :rows="2"
          :placeholder="isEngineerSide ? '回复管理者…' : '回复工程师…'"
          @keydown.ctrl.enter="onSend"
          @keydown.meta.enter="onSend"
        />
        <div style="display: flex; justify-content: space-between; margin-top: 6px">
          <span style="color: #c0c4cc; font-size: 12px">Cmd/Ctrl + Enter 发送</span>
          <el-button type="primary" size="small" :loading="sending" :disabled="!reply.trim()" @click="onSend">
            发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 拒单理由对话框 -->
    <el-dialog v-model="rejectVisible" title="拒单理由" width="420px" append-to-body>
      <el-input
        v-model="rejectReason" type="textarea" :rows="3"
        placeholder="例如：本周已在中环现场，时间排满，建议下周再派 / 当前技能栈不匹配，建议派给云组同事 …"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="sending" :disabled="!rejectReason.trim()" @click="onReject">
          确认拒单
        </el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<style scoped>
.thread {
  max-height: 360px; overflow-y: auto;
  padding: 8px; background: #fafbfc; border-radius: 8px;
  border: 1px solid #ebeef5;
}
.empty { color: #909399; text-align: center; padding: 20px; }
.msg { padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; max-width: 95%; }
.msg-system { background: #f4f4f5; color: #606266; font-size: 13px; }
.msg-pm { background: #ecf5ff; margin-right: 0; margin-left: 0; border-left: 3px solid #409eff; }
.msg-engineer { background: #f0f9eb; margin-left: 5%; border-left: 3px solid #67c23a; }
.msg-hdr { display: flex; justify-content: space-between; gap: 12px; font-size: 11px; color: #909399; margin-bottom: 4px; }
.msg-from { font-weight: 600; }
.msg-time { font-family: 'Courier New', monospace; }
.msg-body { color: #303133; font-size: 13px; line-height: 1.6; white-space: pre-wrap; }

.action-zone {
  margin-top: 12px; padding: 12px;
  background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px;
}
.reply-zone { margin-top: 12px; }
</style>
