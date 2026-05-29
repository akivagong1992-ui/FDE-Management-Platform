<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  attachSkill, detachSkill, getEngineer, revealEngineerId,
  type Engineer,
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
        <el-descriptions-item label="状态">
          <el-tag :type="engineer.status === 'active' ? 'success' : 'info'" size="small">
            {{ engineer.status === 'active' ? '在职' : '已离职' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="入职日">{{ engineer.entry_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="离职日">{{ engineer.exit_date || '—' }}</el-descriptions-item>
      </el-descriptions>

      <el-descriptions v-if="isLead" :column="1" border title="成本（仅 lead/finance 可见）" style="margin-top: 16px">
        <el-descriptions-item label="月服务费 (HK$)">
          {{ engineer.monthly_cost_to_telecom ?? '—' }}
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 24px">
        <div style="font-weight: 600; margin-bottom: 8px">
          持有认证
          <span style="color: #909399; font-size: 12px; font-weight: normal; margin-left: 8px">
            从「能力矩阵管理」全局词库挂载；等级 L1-L3 是认证内禀难度
          </span>
        </div>
        <el-table :data="engineer.skills" size="small">
          <el-table-column prop="skill_category" label="分类" width="110" />
          <el-table-column prop="skill_name" label="认证名称" min-width="180" />
          <el-table-column prop="skill_issuer" label="厂商" width="120">
            <template #default="{ row }">{{ row.skill_issuer || '—' }}</template>
          </el-table-column>
          <el-table-column prop="skill_level" label="等级" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.skill_level" size="small"
                      :type="row.skill_level === 'L3' ? 'success' : row.skill_level === 'L2' ? 'warning' : 'info'">
                {{ row.skill_level }}
              </el-tag>
              <span v-else style="color: #c0c4cc">—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="danger" size="small" @click="onDetachSkill(row.id)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display: flex; gap: 8px; margin-top: 8px">
          <el-select v-model="newSkill.skill_id" placeholder="选择认证" filterable style="flex: 1">
            <el-option
              v-for="s in allSkills" :key="s.id"
              :label="`[${s.category}] ${s.name}${s.level ? ' · ' + s.level : ''}${s.issuer ? ' — ' + s.issuer : ''}`"
              :value="s.id"
            />
          </el-select>
          <el-button type="primary" @click="onAttachSkill">添加</el-button>
        </div>
      </div>

    </div>
  </el-drawer>
</template>
