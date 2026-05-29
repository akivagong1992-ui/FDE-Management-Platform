<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import {
  getCapabilityStats, getEngineerStats, getGrowthTrend,
  type CapabilityStats, type EngineerStats, type GrowthTrend,
} from '@/api/cockpit'

const data = ref<CapabilityStats | null>(null)
const trend = ref<GrowthTrend | null>(null)
const engineers = ref<EngineerStats | null>(null)
let timer: number | undefined

async function load() {
  try {
    const [c, t, e] = await Promise.all([
      getCapabilityStats(), getGrowthTrend(), getEngineerStats(),
    ])
    data.value = c
    trend.value = t
    engineers.value = e
  } catch { /* keep snapshot */ }
}

// Trend line geometry
const TW = 600
const TH = 140
const TPAD = { top: 12, right: 12, bottom: 24, left: 30 }
const tW = TW - TPAD.left - TPAD.right
const tH = TH - TPAD.top - TPAD.bottom

function lineFrom(values: number[], maxY: number) {
  if (values.length === 0) return ''
  return 'M ' + values.map((v, i) => {
    const x = TPAD.left + (tW / Math.max(1, values.length - 1)) * i
    const y = TPAD.top + tH - (v / Math.max(1, maxY)) * tH
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' L ')
}

const skillSeries = computed(() => trend.value?.series.map((p) => p.avg_skill_count) || [])
const skillPath = computed(() => lineFrom(skillSeries.value, Math.max(1, ...skillSeries.value)))
// 「人均技能等级」线已撤掉（个人评级 = 主观打分，已废弃）

// Heatmap: rows = unique Skill.category, cols = L1/L2/L3, cells = distinct engineer count
type SkillLevel = 'L1' | 'L2' | 'L3'
const HEAT_LEVELS: SkillLevel[] = ['L1', 'L2', 'L3']
const heatmap = computed(() => {
  const cats = Array.from(new Set((data.value?.skill_heatmap || []).map((h) => h.category)))
  const grid: Record<string, Record<SkillLevel, number>> = {}
  for (const c of cats) grid[c] = { L1: 0, L2: 0, L3: 0 }
  for (const h of data.value?.skill_heatmap || []) {
    grid[h.category][h.level] = h.count
  }
  return { cats, grid }
})

const heatmapMax = computed(() => Math.max(1, ...(data.value?.skill_heatmap || []).map((h) => h.count)))
const maxIssuer = computed(() => Math.max(1, ...(data.value?.by_issuer || []).map((i) => i.count)))

function heatCellColor(count: number): string {
  if (count === 0) return 'rgba(0,229,255,.05)'
  const ratio = Math.min(count / heatmapMax.value, 1)
  return `rgba(0, 229, 255, ${0.2 + ratio * 0.7})`
}

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card brag">
        <div class="kpi-label">工程师总数</div>
        <div class="kpi-value glow-text"><CountNumber :value="engineers?.total ?? 0" /></div>
        <div class="kpi-sub">在职 {{ engineers?.active ?? 0 }} 人</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">累计持有认证</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.total_skill_assignments ?? 0" /></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">认证覆盖类别数</div>
        <div class="kpi-value glow-text"><CountNumber :value="heatmap.cats.length || 0" /></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">Top 持证工程师</div>
        <div class="top-eng">
          <div v-for="e in (data?.top_skilled_engineers || []).slice(0,3)" :key="e.engineer_id" class="top-eng-row">
            <span>{{ e.name }}</span><span class="top-num">{{ e.skill_count }}</span>
          </div>
          <div v-if="!data?.top_skilled_engineers.length" class="empty-mini">暂无认证</div>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">能力矩阵热力图（类别 × 认证难度）</div>
        <div v-if="heatmap.cats.length === 0" class="empty">暂无认证登记</div>
        <div v-else class="heatmap">
          <div class="hm-header">
            <div class="hm-corner"></div>
            <div v-for="lvl in HEAT_LEVELS" :key="lvl" class="hm-col-hdr">{{ lvl }}</div>
          </div>
          <div v-for="cat in heatmap.cats" :key="cat" class="hm-row">
            <div class="hm-row-hdr">{{ cat }}</div>
            <div v-for="lvl in HEAT_LEVELS" :key="lvl" class="hm-cell"
                 :style="{ background: heatCellColor(heatmap.grid[cat][lvl]) }">
              {{ heatmap.grid[cat][lvl] || '' }}
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">能力成长曲线（季度快照）</div>
        <div v-if="!trend || trend.series.length === 0" class="empty">尚无快照</div>
        <div v-else>
          <svg :viewBox="`0 0 ${TW} ${TH}`" style="width: 100%; height: 140px">
            <line :x1="TPAD.left" :y1="TH - TPAD.bottom" :x2="TW - TPAD.right" :y2="TH - TPAD.bottom"
                  stroke="rgba(0,229,255,.2)" stroke-width="1" />
            <path :d="skillPath" fill="none" stroke="#00e5ff" stroke-width="2" />
            <text v-for="(p, i) in trend.series" :key="i"
                  :x="TPAD.left + (tW / Math.max(1, trend.series.length - 1)) * i" :y="TH - 8"
                  text-anchor="middle" font-size="9" fill="#6b7d97">
              {{ p.date.slice(2, 7) }}
            </text>
          </svg>
          <div class="legend">
            <span><i style="background:#00e5ff"></i>人均技能数</span>
          </div>
          <div class="growth-summary">
            最近 {{ trend.snapshots_count }} 个季度：
            人均认证 <strong class="hi">+{{ trend.growth_delta.avg_skill_count.toFixed(1) }}</strong>
          </div>

          <div class="panel-title" style="margin-top: 16px">认证分布（按厂商）</div>
          <div v-if="!data?.by_issuer.length" class="empty-mini">暂无认证</div>
          <div v-else class="bar-list compact">
            <div v-for="i in data.by_issuer.slice(0, 5)" :key="i.issuer" class="bar-row">
              <div class="bar-label">{{ i.issuer }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: `${(i.count / maxIssuer) * 100}%` }" />
              </div>
              <div class="bar-num">{{ i.count }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px; }
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 10px; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }
.kpi-card.brag .kpi-value { color: var(--cockpit-accent-3); text-shadow: 0 0 8px var(--cockpit-accent-3); }
.kpi-sub { color: var(--cockpit-text-dim); font-size: 11px; margin-top: 4px; }
.legend { display: flex; gap: 12px; margin-top: 4px; color: var(--cockpit-text-dim); font-size: 11px; }
.legend i { display: inline-block; width: 10px; height: 10px; margin-right: 4px; vertical-align: middle; }
.growth-summary { color: var(--cockpit-text); font-size: 12px; margin-top: 8px; }
.hi { color: var(--cockpit-accent-green); font-family: 'Courier New', monospace; }
.compact { gap: 6px; }
.top-eng { display: flex; flex-direction: column; gap: 4px; margin-top: 4px; width: 100%; }
.top-eng-row {
  display: flex; justify-content: space-between; padding: 0 12px;
  color: var(--cockpit-text); font-size: 13px;
}
.top-num { color: var(--cockpit-accent); font-family: 'Courier New', monospace; font-weight: 700; }
.empty-mini { color: var(--cockpit-text-dim); font-size: 12px; }

.lower { flex: 1; display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; min-height: 0; }
.empty { display: flex; align-items: center; justify-content: center; height: calc(100% - 30px); color: var(--cockpit-text-dim); }

.heatmap { margin-top: 12px; }
.hm-header, .hm-row { display: grid; grid-template-columns: 130px repeat(3, 1fr); gap: 6px; margin-bottom: 4px; }
.hm-corner { }
.hm-col-hdr { text-align: center; color: var(--cockpit-accent); font-weight: 600; font-family: 'Courier New', monospace; padding: 4px; }
.hm-row-hdr { color: var(--cockpit-text); font-size: 13px; padding: 8px 0; }
.hm-cell {
  display: flex; align-items: center; justify-content: center;
  padding: 8px; border: 1px solid var(--cockpit-border);
  color: var(--cockpit-text); font-family: 'Courier New', monospace; font-weight: 700;
}

.bar-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 120px 1fr 50px; gap: 8px; align-items: center; }
.bar-label { color: var(--cockpit-text); font-size: 13px; }
.bar-track { height: 12px; background: rgba(0,229,255,.08); border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2)); box-shadow: 0 0 6px var(--cockpit-accent); }
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; }
</style>
