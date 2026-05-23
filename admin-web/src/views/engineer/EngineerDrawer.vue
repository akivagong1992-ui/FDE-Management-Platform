<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  addCertificate, attachSkill, deleteCertificate, detachSkill, getEngineer, revealEngineerId,
  CERT_CATEGORIES, CERT_LEVEL_LABEL,
  type Engineer, type CertLevel,
} from '@/api/engineers'
import { listSkills, type Skill } from '@/api/skills'

const props = defineProps<{ modelValue: boolean; engineerId: number | null }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()
const auth = useAuthStore()

const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin')
const engineer = ref<Engineer | null>(null)
const loading = ref(false)

const revealOpen = ref(false)
const revealedId = ref('')

const allSkills = ref<Skill[]>([])
const newSkill = ref<{ skill_id: number | null }>({ skill_id: null })

interface NewCertForm {
  name: string; issuer: string; cert_number: string
  issue_date: string; expiry_date: string
  cert_level: CertLevel | ''
  cert_category: string
}
const blankCert = (): NewCertForm => ({
  name: '', issuer: '', cert_number: '',
  issue_date: '', expiry_date: '',
  cert_level: '', cert_category: '',
})
const newCert = ref<NewCertForm>(blankCert())

const CERT_LEVEL_TAG: Record<CertLevel, 'info' | 'warning' | 'danger'> = {
  L1: 'info', L2: 'warning', L3: 'danger',
}

async function refresh() {
  if (!props.engineerId) return
  loading.value = true
  try {
    engineer.value = await getEngineer(props.engineerId)
    allSkills.value = await listSkills()
  } finally {
    loading.value = false
  }
}

watch(() => [props.modelValue, props.engineerId], async ([open]) => {
  if (open && props.engineerId) {
    revealedId.value = ''
    revealOpen.value = false
    await refresh()
  }
})

async function onReveal() {
  if (!props.engineerId) return
  await ElMessageBox.confirm('查看明文证件号将记录审计日志。是否继续？', '敏感操作', { type: 'warning' })
  const r = await revealEngineerId(props.engineerId)
  revealedId.value = r.id_doc_number
  revealOpen.value = true
}

async function onAttachSkill() {
  if (!props.engineerId || !newSkill.value.skill_id) {
    ElMessage.warning('选择技能')
    return
  }
  await attachSkill(props.engineerId, { skill_id: newSkill.value.skill_id })
  newSkill.value = { skill_id: null }
  await refresh()
}

async function onDetachSkill(esId: number) {
  if (!props.engineerId) return
  await detachSkill(props.engineerId, esId)
  await refresh()
}

async function onAddCert() {
  if (!props.engineerId || !newCert.value.name) {
    ElMessage.warning('证书名必填')
    return
  }
  if (!newCert.value.cert_level || !newCert.value.cert_category) {
    ElMessage.warning('级别 + 类别必填（决定能力矩阵热力图位置）')
    return
  }
  const payload: Record<string, unknown> = { ...newCert.value }
  if (!payload.issue_date) payload.issue_date = null
  if (!payload.expiry_date) payload.expiry_date = null
  await addCertificate(props.engineerId, payload as any)
  newCert.value = blankCert()
  await refresh()
}

async function onDeleteCert(id: number) {
  if (!props.engineerId) return
  await deleteCertificate(props.engineerId, id)
  await refresh()
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    direction="rtl" size="720px"
    :title="engineer ? `${engineer.full_name} · 详情` : '加载中…'"
  >
    <div v-loading="loading" v-if="engineer">
      <el-descriptions :column="2" border title="基本信息">
        <el-descriptions-item label="Vendor">{{ engineer.vendor_name }}</el-descriptions-item>
        <el-descriptions-item label="签约形态">
          <el-tag>{{ engineer.employment_form === 'vendor_direct' ? 'Vendor 直签' : 'Vendor 通过劳务公司' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="劳务公司" v-if="engineer.employment_form === 'vendor_via_labor'" :span="2">
          {{ engineer.labor_company || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="姓名">{{ engineer.full_name }}</el-descriptions-item>
        <el-descriptions-item label="英文名">{{ engineer.english_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ engineer.mobile || '—' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ engineer.email || '—' }}</el-descriptions-item>
        <el-descriptions-item label="证件类型">{{ engineer.id_doc_type || '—' }}</el-descriptions-item>
        <el-descriptions-item label="证件号">
          <span v-if="!revealOpen">{{ engineer.id_doc_number_masked || '—' }}</span>
          <span v-else style="color: #f56c6c; font-weight: 600">{{ revealedId }}</span>
          <el-button
            v-if="isLead && engineer.id_doc_number_masked && !revealOpen"
            link type="primary" size="small" style="margin-left: 8px"
            @click="onReveal"
          >查看</el-button>
          <el-button
            v-if="revealOpen" link size="small" style="margin-left: 8px"
            @click="revealOpen = false"
          >隐藏</el-button>
        </el-descriptions-item>
        <el-descriptions-item label="状态"><el-tag>{{ engineer.status }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="入场">{{ engineer.entry_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="离场">{{ engineer.exit_date || '—' }}</el-descriptions-item>
      </el-descriptions>

      <el-descriptions v-if="isLead" :column="2" border title="成本（仅 lead/finance 可见）" style="margin-top: 16px">
        <el-descriptions-item label="月服务费 (HK$)">
          {{ engineer.monthly_cost_to_telecom ?? '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="Vendor 真实人工成本 (HK$)">
          <span style="color: #e6a23c">{{ engineer.monthly_real_cost ?? '—' }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 24px">
        <div style="font-weight: 600; margin-bottom: 8px">
          技能清单
          <span style="color: #909399; font-size: 12px; font-weight: normal; margin-left: 8px">
            仅记录会/不会，水平由下方厂商认证体现
          </span>
        </div>
        <el-table :data="engineer.skills" size="small">
          <el-table-column prop="skill_category" label="分类" width="110" />
          <el-table-column prop="skill_name" label="技能" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="onDetachSkill(row.id)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display: flex; gap: 8px; margin-top: 8px">
          <el-select v-model="newSkill.skill_id" placeholder="选择技能" filterable style="flex: 1">
            <el-option v-for="s in allSkills" :key="s.id" :label="`[${s.category}] ${s.name}`" :value="s.id" />
          </el-select>
          <el-button type="primary" @click="onAttachSkill">添加</el-button>
        </div>
      </div>

      <div style="margin-top: 24px">
        <div style="font-weight: 600; margin-bottom: 8px">
          厂商认证（决定工程师水平）
          <span style="color: #909399; font-size: 12px; font-weight: normal; margin-left: 8px">
            初级 = L1，中级 = L2，高级 = L3
          </span>
        </div>
        <el-table :data="engineer.certificates" size="small">
          <el-table-column prop="name" label="证书" min-width="180" />
          <el-table-column prop="issuer" label="颁发机构" width="120" />
          <el-table-column prop="cert_category" label="类别" width="100">
            <template #default="{ row }">
              <span v-if="row.cert_category">{{ row.cert_category }}</span>
              <span v-else style="color: #c0c4cc">—</span>
            </template>
          </el-table-column>
          <el-table-column label="级别" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.cert_level" :type="CERT_LEVEL_TAG[row.cert_level as CertLevel]" size="small">
                {{ CERT_LEVEL_LABEL[row.cert_level as CertLevel] }}
              </el-tag>
              <span v-else style="color: #c0c4cc">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="expiry_date" label="到期" width="110" />
          <el-table-column label="操作" width="70">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="onDeleteCert(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px; margin-top: 8px">
          <el-input v-model="newCert.name" placeholder="证书名（CCIE / CISSP / 华为 HCIA 等）" />
          <el-input v-model="newCert.issuer" placeholder="颁发机构" />
          <el-select v-model="newCert.cert_category" placeholder="类别 (必选)">
            <el-option v-for="c in CERT_CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
          <el-select v-model="newCert.cert_level" placeholder="级别 (必选)">
            <el-option label="L1 初级" value="L1" />
            <el-option label="L2 中级" value="L2" />
            <el-option label="L3 高级" value="L3" />
          </el-select>
        </div>
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 8px; margin-top: 8px">
          <el-input v-model="newCert.cert_number" placeholder="证书编号 (可选)" />
          <el-date-picker v-model="newCert.issue_date" type="date" placeholder="颁发日 (可选)" value-format="YYYY-MM-DD" style="width: 100%" />
          <el-date-picker v-model="newCert.expiry_date" type="date" placeholder="到期日 (可选)" value-format="YYYY-MM-DD" style="width: 100%" />
        </div>
        <div style="text-align: right; margin-top: 8px">
          <el-button type="primary" @click="onAddCert">添加证书</el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>
