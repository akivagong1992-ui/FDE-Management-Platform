<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getCapabilityStats, type CapabilityStats } from '@/api/cockpit'

const data = ref<CapabilityStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getCapabilityStats() } catch { /* keep */ } }

// Heatmap: rows = unique categories, cols = level 1-5, cells = engineer count
const heatmap = computed(() => {
  const cats = Array.from(new Set((data.value?.skill_heatmap || []).map((h) => h.category)))
  const grid: Record<string, Record<number, number>> = {}
  for (const c of cats) grid[c] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
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
        <div class="kpi-label">累计外部证书</div>
        <div class="kpi-value glow-text">{{ data?.total_certificates ?? '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">技能分类数</div>
        <div class="kpi-value glow-text">{{ heatmap.cats.length || '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">认证机构数</div>
        <div class="kpi-value glow-text">{{ data?.by_issuer.length ?? '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">Top 持证工程师</div>
        <div class="top-eng">
          <div v-for="e in (data?.top_certified_engineers || []).slice(0,3)" :key="e.engineer_id" class="top-eng-row">
            <span>{{ e.name }}</span><span class="top-num">{{ e.cert_count }}</span>
          </div>
          <div v-if="!data?.top_certified_engineers.length" class="empty-mini">暂无证书</div>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">技能矩阵热力图（类别 × L1-L5）</div>
        <div v-if="heatmap.cats.length === 0" class="empty">暂无技能登记</div>
        <div v-else class="heatmap">
          <div class="hm-header">
            <div class="hm-corner"></div>
            <div v-for="lvl in 5" :key="lvl" class="hm-col-hdr">L{{ lvl }}</div>
          </div>
          <div v-for="cat in heatmap.cats" :key="cat" class="hm-row">
            <div class="hm-row-hdr">{{ cat }}</div>
            <div v-for="lvl in 5" :key="lvl" class="hm-cell"
                 :style="{ background: heatCellColor(heatmap.grid[cat][lvl]) }">
              {{ heatmap.grid[cat][lvl] || '' }}
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">证书分布（按机构）</div>
        <div v-if="!data?.by_issuer.length" class="empty">暂无证书数据</div>
        <div v-else class="bar-list">
          <div v-for="i in data.by_issuer" :key="i.issuer" class="bar-row">
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
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px; }
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 10px; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }
.kpi-card.brag .kpi-value { color: var(--cockpit-accent-3); text-shadow: 0 0 8px var(--cockpit-accent-3); }
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
.hm-header, .hm-row { display: grid; grid-template-columns: 130px repeat(5, 1fr); gap: 4px; margin-bottom: 4px; }
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
.bar-track { height: 12px; background: rgba(0,229,255,.08); border: 1px solid var(--cockpit-border); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2)); box-shadow: 0 0 6px var(--cockpit-accent); }
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; }
</style>
