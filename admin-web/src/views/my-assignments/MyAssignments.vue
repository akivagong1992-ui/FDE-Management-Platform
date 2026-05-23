<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  APPROVAL_LABEL, APPROVAL_TAG_TYPE,
  listAssignments,
  type ApprovalStatus, type Assignment,
} from '@/api/assignments'
import AssignmentDrawer from '../engineer/AssignmentDrawer.vue'

const rows = ref<Assignment[]>([])
const loading = ref(false)
const tab = ref<'pending' | 'accepted' | 'rejected' | 'all'>('pending')

const drawerOpen = ref(false)
const drawerId = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    rows.value = await listAssignments()
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  if (tab.value === 'all') return rows.value
  return rows.value.filter((a) => a.approval_status === tab.value)
})
const pendingCount = computed(() => rows.value.filter((a) => a.approval_status === 'pending').length)
const acceptedCount = computed(() => rows.value.filter((a) => a.approval_status === 'accepted').length)
const rejectedCount = computed(() => rows.value.filter((a) => a.approval_status === 'rejected').length)

function openDrawer(a: Assignment) {
  drawerId.value = a.id
  drawerOpen.value = true
}

const STATUS_LABEL: Record<string, string> = {
  planned: '计划中', in_progress: '进行中', ended: '已结束', cancelled: '已取消',
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">我的派单</span>
        <span style="color: #909399; font-size: 12px">
          待确认 <strong style="color: #e6a23c">{{ pendingCount }}</strong> 条 ·
          已接 <strong style="color: #67c23a">{{ acceptedCount }}</strong> 条 ·
          已拒 <strong style="color: #f56c6c">{{ rejectedCount }}</strong> 条
        </span>
      </div>
    </template>

    <el-radio-group v-model="tab" size="default" style="margin-bottom: 16px">
      <el-radio-button label="pending">
        待确认 <el-badge v-if="pendingCount > 0" :value="pendingCount" type="warning" />
      </el-radio-button>
      <el-radio-button label="accepted">已接单</el-radio-button>
      <el-radio-button label="rejected">已拒单</el-radio-button>
      <el-radio-button label="all">全部</el-radio-button>
    </el-radio-group>

    <div v-loading="loading">
      <div v-if="filtered.length === 0" class="empty">
        <template v-if="tab === 'pending'">🎉 没有待确认的派单</template>
        <template v-else>暂无</template>
      </div>
      <div v-else class="card-list">
        <el-card v-for="a in filtered" :key="a.id" class="assn-card" shadow="hover">
          <div class="row-1">
            <span class="proj">{{ a.project_name }}</span>
            <el-tag :type="APPROVAL_TAG_TYPE[a.approval_status as ApprovalStatus]" size="small">
              {{ APPROVAL_LABEL[a.approval_status as ApprovalStatus] }}
            </el-tag>
          </div>
          <div class="row-2">
            <span><b>角色：</b>{{ a.role || '—' }}</span>
            <span><b>阶段：</b>{{ STATUS_LABEL[a.status] || a.status }}</span>
            <span><b>计划：</b>{{ a.planned_start_date || '—' }} → {{ a.planned_end_date || '—' }}</span>
          </div>
          <div class="row-3">
            <span class="msg-count">对话 {{ a.message_count }} 条</span>
            <el-button
              :type="a.approval_status === 'pending' ? 'warning' : 'primary'"
              size="small"
              @click="openDrawer(a)"
            >
              {{ a.approval_status === 'pending' ? '查看 / 确认' : '查看详情' }}
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <AssignmentDrawer
      v-model="drawerOpen"
      :assignment-id="drawerId"
      @changed="load"
    />
  </el-card>
</template>

<style scoped>
.empty {
  padding: 60px 0; text-align: center; color: #909399;
}
.card-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 12px;
}
.assn-card { border-radius: 10px; }
.row-1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.proj { font-weight: 600; color: #303133; font-size: 15px; }
.row-2 {
  display: flex; flex-wrap: wrap; gap: 12px;
  color: #606266; font-size: 13px; margin-bottom: 10px;
}
.row-3 {
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid #f0f0f0; padding-top: 8px;
}
.msg-count { color: #909399; font-size: 12px; }
</style>
