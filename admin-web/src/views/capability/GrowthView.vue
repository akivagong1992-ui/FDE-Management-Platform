<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { teamTrend, type TeamTrendPoint } from '@/api/capability'

const trend = ref<TeamTrendPoint[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    trend.value = await teamTrend()
  } finally {
    loading.value = false
  }
}

// Color palette aligned across KPI cards + chart lines
const COLOR_SKILL = '#409eff'
const COLOR_LEVEL = '#e6a23c'
const COLOR_CERT = '#67c23a'

// Simple SVG line chart helpers
const W = 700
const H = 220
const padding = { top: 16, right: 16, bottom: 30, left: 40 }
const chartW = W - padding.left - padding.right
const chartH = H - padding.top - padding.bottom

function polyline(points: number[], maxY: number): { d: string; pts: { x: number; y: number; v: number }[] } {
  if (points.length === 0) return { d: '', pts: [] }
  const pts = points.map((v, i) => {
    const x = padding.left + (chartW / Math.max(1, points.length - 1)) * i
    const y = padding.top + chartH - (v / Math.max(1, maxY)) * chartH
    return { x, y, v }
  })
  const d = 'M ' + pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ')
  return { d, pts }
}

const skillSeries = computed(() => trend.value.map((p) => p.avg_skill_count))
const levelSeries = computed(() => trend.value.map((p) => p.avg_skill_level))
const certSeries = computed(() => trend.value.map((p) => p.avg_cert_count))

const skillLine = computed(() => polyline(skillSeries.value, Math.max(1, ...skillSeries.value)))
const levelLine = computed(() => polyline(levelSeries.value, 3))
const certLine = computed(() => polyline(certSeries.value, Math.max(1, ...certSeries.value)))

const earliest = computed(() => trend.value[0])
const latest = computed(() => trend.value[trend.value.length - 1])

onMounted(load)
</script>

<template>
  <div class="growth-page">
    <!-- KPI 三件套 — 色彩与下方曲线一一对应 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">
            <span class="dot" :style="{ background: COLOR_SKILL }" />
            人均技能数
          </div>
          <div class="kpi-value" :style="{ color: COLOR_SKILL }">
            {{ latest?.avg_skill_count?.toFixed(2) ?? '—' }}
          </div>
          <div v-if="earliest && latest" class="kpi-delta">
            ▲ +{{ (latest.avg_skill_count - earliest.avg_skill_count).toFixed(2) }} <span class="kpi-delta-since">vs 起点</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">
            <span class="dot" :style="{ background: COLOR_LEVEL }" />
            人均技能等级
          </div>
          <div class="kpi-value" :style="{ color: COLOR_LEVEL }">
            L{{ latest?.avg_skill_level?.toFixed(2) ?? '—' }}
          </div>
          <div v-if="earliest && latest" class="kpi-delta">
            ▲ +{{ (latest.avg_skill_level - earliest.avg_skill_level).toFixed(2) }} <span class="kpi-delta-since">vs 起点</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">
            <span class="dot" :style="{ background: COLOR_CERT }" />
            人均外部证书
          </div>
          <div class="kpi-value" :style="{ color: COLOR_CERT }">
            {{ latest?.avg_cert_count?.toFixed(2) ?? '—' }}
          </div>
          <div v-if="earliest && latest" class="kpi-delta">
            ▲ +{{ (latest.avg_cert_count - earliest.avg_cert_count).toFixed(2) }} <span class="kpi-delta-since">vs 起点</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 团队成长曲线 — 头部内联 legend，色彩与上方 KPI 同步 -->
    <el-card v-loading="loading" class="chart-card">
      <template #header>
        <div class="chart-header">
          <span class="chart-title">团队成长曲线</span>
          <div class="legend">
            <span><span class="legend-dot" :style="{ background: COLOR_SKILL }" />人均技能数</span>
            <span><span class="legend-dot" :style="{ background: COLOR_LEVEL }" />人均等级 (L1–3)</span>
            <span><span class="legend-dot" :style="{ background: COLOR_CERT }" />人均证书数</span>
          </div>
        </div>
      </template>
      <svg v-if="trend.length > 0" :viewBox="`0 0 ${W} ${H}`" style="width: 100%; max-height: 260px">
        <line :x1="padding.left" :y1="H - padding.bottom" :x2="W - padding.right" :y2="H - padding.bottom"
              stroke="#dcdfe6" stroke-width="1" />
        <line :x1="padding.left" :y1="padding.top" :x2="padding.left" :y2="H - padding.bottom"
              stroke="#dcdfe6" stroke-width="1" />
        <path :d="skillLine.d" fill="none" :stroke="COLOR_SKILL" stroke-width="2" />
        <circle v-for="(p, i) in skillLine.pts" :key="`s${i}`" :cx="p.x" :cy="p.y" r="3" :fill="COLOR_SKILL" />
        <path :d="levelLine.d" fill="none" :stroke="COLOR_LEVEL" stroke-width="2" />
        <circle v-for="(p, i) in levelLine.pts" :key="`l${i}`" :cx="p.x" :cy="p.y" r="3" :fill="COLOR_LEVEL" />
        <path :d="certLine.d" fill="none" :stroke="COLOR_CERT" stroke-width="2" />
        <circle v-for="(p, i) in certLine.pts" :key="`c${i}`" :cx="p.x" :cy="p.y" r="3" :fill="COLOR_CERT" />
        <text v-for="(p, i) in trend" :key="`x${i}`"
              :x="padding.left + (chartW / Math.max(1, trend.length - 1)) * i" :y="H - 12"
              text-anchor="middle" font-size="11" fill="#909399">
          {{ p.snapshot_date.slice(2, 7) }}
        </text>
      </svg>
      <el-empty v-else description="暂无数据" :image-size="80" />
    </el-card>
  </div>
</template>

<style scoped>
.growth-page { display: flex; flex-direction: column; gap: 16px; }

.kpi-row { margin-bottom: 0; }
.kpi-card { height: 100%; }
.kpi-label {
  display: flex; align-items: center; gap: 6px;
  color: #909399; font-size: 13px;
}
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.kpi-value { font-size: 28px; font-weight: 600; margin-top: 10px; line-height: 1.2; }
.kpi-delta { font-size: 12px; color: #67c23a; margin-top: 6px; }
.kpi-delta-since { color: #c0c4cc; margin-left: 4px; }

.chart-card { margin-top: 0; }
.chart-header {
  display: flex; justify-content: space-between; align-items: center;
}
.chart-title { font-weight: 600; color: #303133; }
.legend {
  display: flex; gap: 16px; font-size: 12px; color: #606266;
}
.legend-dot {
  display: inline-block; width: 10px; height: 10px;
  border-radius: 2px; margin-right: 4px; vertical-align: middle;
}
</style>
