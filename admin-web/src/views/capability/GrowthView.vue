<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  listSnapshots, teamTrend, triggerSnapshot,
  type SkillSnapshot, type TeamTrendPoint,
} from '@/api/capability'

const auth = useAuthStore()
const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin')

const trend = ref<TeamTrendPoint[]>([])
const snapshots = ref<SkillSnapshot[]>([])
const loading = ref(false)
const triggering = ref(false)

async function load() {
  loading.value = true
  try {
    trend.value = await teamTrend()
    snapshots.value = await listSnapshots()
  } finally {
    loading.value = false
  }
}

async function onTrigger() {
  await ElMessageBox.confirm(
    '将为所有在场工程师拍一份当日快照。已存在的会自动跳过。',
    '触发能力快照', { type: 'info' },
  )
  triggering.value = true
  try {
    const r = await triggerSnapshot()
    ElMessage.success(`已拍 ${r.snapshot_date} 快照：新增 ${r.created} 条，跳过 ${r.skipped} 条`)
    await load()
  } finally {
    triggering.value = false
  }
}

// Latest per-engineer (group by engineer_id, take first since list is desc by date)
const latestPerEngineer = computed(() => {
  const seen = new Set<number>()
  const result: SkillSnapshot[] = []
  for (const s of snapshots.value) {
    if (!seen.has(s.engineer_id)) {
      seen.add(s.engineer_id)
      result.push(s)
    }
  }
  return result
})

// Simple SVG line chart helpers
const W = 700
const H = 200
const padding = { top: 16, right: 16, bottom: 30, left: 40 }
const chartW = W - padding.left - padding.right
const chartH = H - padding.top - padding.bottom

function polyline(points: number[], maxY: number, color: string): { d: string; pts: { x: number; y: number; v: number }[] } {
  if (points.length === 0) return { d: '', pts: [] }
  const pts = points.map((v, i) => {
    const x = padding.left + (chartW / Math.max(1, points.length - 1)) * i
    const y = padding.top + chartH - (v / Math.max(1, maxY)) * chartH
    return { x, y, v }
  })
  const d = 'M ' + pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ')
  void color
  return { d, pts }
}

const skillSeries = computed(() => trend.value.map((p) => p.avg_skill_count))
const levelSeries = computed(() => trend.value.map((p) => p.avg_skill_level))
const certSeries = computed(() => trend.value.map((p) => p.avg_cert_count))

const skillLine = computed(() => polyline(skillSeries.value, Math.max(1, ...skillSeries.value), '#409eff'))
const levelLine = computed(() => polyline(levelSeries.value, 5, '#e6a23c'))
const certLine = computed(() => polyline(certSeries.value, Math.max(1, ...certSeries.value), '#67c23a'))

const earliest = computed(() => trend.value[0])
const latest = computed(() => trend.value[trend.value.length - 1])

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: flex-end; margin-bottom: 12px">
      <el-button type="primary" :loading="triggering" :disabled="!isLead" @click="onTrigger">
        📸 拍今日快照
      </el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="color: #909399; font-size: 13px">快照次数</div>
          <div style="font-size: 26px; font-weight: 600; margin-top: 8px">{{ trend.length }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="color: #909399; font-size: 13px">人均技能数</div>
          <div style="font-size: 26px; font-weight: 600; color: #409eff; margin-top: 8px">
            {{ latest?.avg_skill_count ?? '—' }}
          </div>
          <div v-if="earliest && latest" style="font-size: 12px; color: #67c23a; margin-top: 4px">
            ▲ +{{ (latest.avg_skill_count - earliest.avg_skill_count).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="color: #909399; font-size: 13px">人均技能等级</div>
          <div style="font-size: 26px; font-weight: 600; color: #e6a23c; margin-top: 8px">
            L{{ latest?.avg_skill_level?.toFixed(2) ?? '—' }}
          </div>
          <div v-if="earliest && latest" style="font-size: 12px; color: #67c23a; margin-top: 4px">
            ▲ +{{ (latest.avg_skill_level - earliest.avg_skill_level).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="color: #909399; font-size: 13px">人均外部证书</div>
          <div style="font-size: 26px; font-weight: 600; color: #67c23a; margin-top: 8px">
            {{ latest?.avg_cert_count?.toFixed(2) ?? '—' }}
          </div>
          <div v-if="earliest && latest" style="font-size: 12px; color: #67c23a; margin-top: 4px">
            ▲ +{{ (latest.avg_cert_count - earliest.avg_cert_count).toFixed(2) }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-loading="loading" style="margin-top: 16px">
      <template #header>团队成长曲线</template>
      <svg v-if="trend.length > 0" :viewBox="`0 0 ${W} ${H}`" style="width: 100%; max-height: 240px">
        <!-- axes -->
        <line :x1="padding.left" :y1="H - padding.bottom" :x2="W - padding.right" :y2="H - padding.bottom"
              stroke="#dcdfe6" stroke-width="1" />
        <line :x1="padding.left" :y1="padding.top" :x2="padding.left" :y2="H - padding.bottom"
              stroke="#dcdfe6" stroke-width="1" />
        <!-- skill_count line -->
        <path :d="skillLine.d" fill="none" stroke="#409eff" stroke-width="2" />
        <circle v-for="(p, i) in skillLine.pts" :key="`s${i}`" :cx="p.x" :cy="p.y" r="3" fill="#409eff" />
        <!-- level line -->
        <path :d="levelLine.d" fill="none" stroke="#e6a23c" stroke-width="2" />
        <circle v-for="(p, i) in levelLine.pts" :key="`l${i}`" :cx="p.x" :cy="p.y" r="3" fill="#e6a23c" />
        <!-- cert line -->
        <path :d="certLine.d" fill="none" stroke="#67c23a" stroke-width="2" />
        <circle v-for="(p, i) in certLine.pts" :key="`c${i}`" :cx="p.x" :cy="p.y" r="3" fill="#67c23a" />
        <!-- x labels -->
        <text v-for="(p, i) in trend" :key="`x${i}`"
              :x="padding.left + (chartW / Math.max(1, trend.length - 1)) * i" :y="H - 12"
              text-anchor="middle" font-size="11" fill="#909399">
          {{ p.snapshot_date.slice(2, 7) }}
        </text>
      </svg>
      <el-empty v-else description="尚未拍快照 — 点右上「📸 拍今日快照」开始" />

      <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 13px; color: #606266">
        <span><span style="display:inline-block;width:12px;height:12px;background:#409eff;margin-right:4px"></span>人均技能数</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#e6a23c;margin-right:4px"></span>人均等级 (L1-5)</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#67c23a;margin-right:4px"></span>人均证书数</span>
      </div>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>最新快照（每工程师最新一条）</template>
      <el-table :data="latestPerEngineer" stripe size="small" max-height="400">
        <el-table-column prop="engineer_name" label="工程师" width="120" />
        <el-table-column prop="snapshot_date" label="快照日" width="120" sortable />
        <el-table-column label="级别" width="80">
          <template #default="{ row }">L{{ row.level ?? '—' }}</template>
        </el-table-column>
        <el-table-column prop="skill_count" label="技能数" width="100" sortable />
        <el-table-column label="平均等级" width="100" sortable>
          <template #default="{ row }">{{ Number(row.avg_level).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="cert_count" label="证书数" width="100" sortable />
      </el-table>
    </el-card>
  </div>
</template>
