<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  getProject, listTransferLogs, transferSales,
  BENCHMARK_BASIS_LABELS, BID_OUTCOME_LABELS, BID_OUTCOME_TYPES,
  type BidOutcome, type Project, type TransferLog, type TransferReason,
} from '@/api/projects'
import { listSalesPersons, type SalesPerson } from '@/api/salesPersons'
import { fmt2 } from '@/utils/format'

const props = defineProps<{ modelValue: boolean; projectId: number | null }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; refresh: [] }>()
const auth = useAuthStore()
const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin')

const project = ref<Project | null>(null)
const logs = ref<TransferLog[]>([])
const sales = ref<SalesPerson[]>([])
const loading = ref(false)

const transferDialog = ref(false)
const transferForm = ref<{ to_sales_person_id: number | null; reason: TransferReason; reason_note: string }>({
  to_sales_person_id: null, reason: 'resignation', reason_note: '',
})

const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收', closing: '收尾', archived: '归档',
}
const BASIS_LABEL: Record<string, string> = {
  outsource_equiv: '等同外包服务所抵消的成本（默认）',
  other: '其他（备注必填）',
}

async function refresh() {
  if (!props.projectId) return
  loading.value = true
  try {
    project.value = await getProject(props.projectId)
    logs.value = await listTransferLogs(props.projectId)
    if (sales.value.length === 0) sales.value = await listSalesPersons(true)
  } finally {
    loading.value = false
  }
}

watch(() => [props.modelValue, props.projectId], async ([open]) => {
  if (open && props.projectId) await refresh()
})

function openTransfer() {
  if (!project.value) return
  transferForm.value = { to_sales_person_id: null, reason: 'resignation', reason_note: '' }
  transferDialog.value = true
}

async function onConfirmTransfer() {
  if (!props.projectId || !transferForm.value.to_sales_person_id) {
    ElMessage.warning('请选择目标销售')
    return
  }
  await ElMessageBox.confirm('转移销售将更新此项目利润口径 B 的归属，操作不可撤销但会留审计日志。是否继续？', '确认转移', { type: 'warning' })
  await transferSales(props.projectId, {
    to_sales_person_id: transferForm.value.to_sales_person_id,
    reason: transferForm.value.reason,
    reason_note: transferForm.value.reason_note || undefined,
  })
  ElMessage.success('已转移')
  transferDialog.value = false
  await refresh()
  emit('refresh')
}

function salesNameById(id: number): string {
  const sp = sales.value.find((s) => s.id === id)
  return sp ? sp.name : `#${id}`
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    direction="rtl" size="640px"
    :title="project ? `${project.name} · 详情` : '加载中…'"
  >
    <div v-loading="loading" v-if="project">
      <el-descriptions :column="2" border title="基本信息">
        <el-descriptions-item label="编号">{{ project.code || '—' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag>{{ STATUS_LABEL[project.status] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="项目类型">
          <el-tag :type="project.kind === 'revenue' ? 'success' : 'warning'">
            {{ project.kind === 'revenue' ? '有收入项目' : '无收入项目 (仅入 C 口径)' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="投标结果">
          <span v-if="project.kind === 'no_revenue'" style="color: #c0c4cc">NA</span>
          <template v-else>
            <el-tag :type="BID_OUTCOME_TYPES[project.bid_outcome as BidOutcome]">
              {{ BID_OUTCOME_LABELS[project.bid_outcome as BidOutcome] || project.bid_outcome }}
            </el-tag>
            <span v-if="project.bid_outcome !== 'won'"
                  style="color: #909399; font-size: 12px; margin-left: 8px">
              （不计入驾驶舱降本）
            </span>
          </template>
        </el-descriptions-item>
        <el-descriptions-item label="需求方">{{ project.need_party_name }}</el-descriptions-item>
        <el-descriptions-item label="销售人员">
          {{ project.sales_person_name }}
          <el-tag v-if="!project.sales_person_active" type="info" size="small" style="margin-left: 4px">已停用</el-tag>
          <el-button v-if="isLead" link type="primary" size="small" style="margin-left: 8px" @click="openTransfer">转移销售</el-button>
        </el-descriptions-item>
        <el-descriptions-item label="计划开始">{{ project.planned_start_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="计划结束">{{ project.planned_end_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="实际开始">{{ project.actual_start_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="实际结束">{{ project.actual_end_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ project.description || '—' }}</el-descriptions-item>
      </el-descriptions>

      <el-descriptions :column="1" border title="价值估算（C 口径）" style="margin-top: 16px">
        <el-descriptions-item label="传统外包模式估算">
          <span v-if="project.outsource_benchmark_amount">HK$ {{ fmt2(project.outsource_benchmark_amount) }}</span>
          <span v-else style="color: #909399">—</span>
          <span style="color: #909399; font-size: 12px; margin-left: 8px">
            （如果当年走老外包，估算花多少）
          </span>
        </el-descriptions-item>
        <el-descriptions-item v-if="project.benchmark_basis" label="价格来源依据">
          <el-tag :type="project.benchmark_basis === 'vendor_quote' ? 'success' : 'primary'">
            {{ BENCHMARK_BASIS_LABELS[project.benchmark_basis] }}
          </el-tag>
          <div v-if="project.benchmark_basis_note" style="color: #606266; margin-top: 4px; font-size: 12px">
            {{ project.benchmark_basis_note }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item v-if="project.kind === 'no_revenue'" label="自动计算的效益金额">
          <span style="color: #e6a23c; font-weight: 600">HK$ {{ fmt2(project.value_created_computed) }}</span>
          <span style="color: #909399; font-size: 12px; margin-left: 8px">
            = 服务商价格（项目完成时自动计入）
          </span>
        </el-descriptions-item>
        <el-descriptions-item v-if="project.kind === 'revenue'" label="自动计算的效益金额">
          <span v-if="project.value_created_computed" style="color: #e6a23c; font-weight: 600">
            HK$ {{ fmt2(project.value_created_computed) }}
          </span>
          <span v-else style="color: #909399">
            —（须 <strong>投标结果=已中标</strong>）
          </span>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            = 服务商价格 − 团队入账（Σ 该项目收入记录的 amount）
          </div>
        </el-descriptions-item>
        <el-descriptions-item v-if="project.kind === 'no_revenue'" label="价值依据">
          {{ BASIS_LABEL[project.value_created_basis || 'outsource_equiv'] }}
        </el-descriptions-item>
        <el-descriptions-item v-if="project.kind === 'no_revenue' && project.value_created_note" label="依据说明">
          {{ project.value_created_note }}
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 24px">
        <div style="font-weight: 600; margin-bottom: 8px">销售转移历史</div>
        <el-empty v-if="logs.length === 0" :image-size="60" description="无转移记录" />
        <el-table v-else :data="logs" size="small">
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column label="从">
            <template #default="{ row }">{{ salesNameById(row.from_sales_person_id) }}</template>
          </el-table-column>
          <el-table-column label="到">
            <template #default="{ row }">{{ salesNameById(row.to_sales_person_id) }}</template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" width="100" />
          <el-table-column prop="reason_note" label="备注" />
        </el-table>
      </div>
    </div>

    <el-dialog v-model="transferDialog" title="转移销售" width="440px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="目标销售">
          <el-select v-model="transferForm.to_sales_person_id" filterable placeholder="选择在岗销售" style="width: 100%">
            <el-option
              v-for="s in sales.filter((sp) => sp.id !== project?.sales_person_id)"
              :key="s.id" :label="s.name" :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-select v-model="transferForm.reason" style="width: 100%">
            <el-option label="离职" value="resignation" />
            <el-option label="调岗" value="role_change" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="transferForm.reason_note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferDialog = false">取消</el-button>
        <el-button type="primary" @click="onConfirmTransfer">确认转移</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>
