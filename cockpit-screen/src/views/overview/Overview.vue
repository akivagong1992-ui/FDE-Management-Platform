<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getOverview, getSavingsAndValue, type OverviewKpi, type SavingsAndValue } from '@/api/cockpit'

const overview = ref<OverviewKpi | null>(null)
const sav = ref<SavingsAndValue | null>(null)
let refreshTimer: number | undefined

async function load() {
  try {
    const [o, s] = await Promise.all([getOverview(), getSavingsAndValue()])
    overview.value = o
    sav.value = s
  } catch {
    /* keep last successful snapshot on transient errors */
  }
}

function fmt10k(n: number | undefined | null): string {
  if (!n && n !== 0) return '—'
  return (n / 10000).toLocaleString('en-HK', { maximumFractionDigits: 1 })
}

function fmtInt(n: number | undefined | null): string {
  if (n == null) return '—'
  return Math.round(n).toLocaleString('en-HK')
}

// C-tier number split for the brag tile
const cTotal = computed(() => sav.value?.total_c_view ?? 0)
const cSavings = computed(() => sav.value?.savings_from_revenue_projects ?? 0)
const cValue = computed(() => sav.value?.value_created_from_no_revenue_projects ?? 0)

const kpis = computed(() => [
  { label: '在管项目', value: fmtInt(overview.value?.active_projects), unit: '' },
  { label: '为公司创造的价值', value: fmt10k(cTotal.value), unit: '万 HKD', brag: true },
  { label: '团队规模', value: fmtInt(overview.value?.team_size), unit: '' },
  { label: '按时交付率', value: overview.value ? `${(overview.value.on_time_delivery_rate * 100).toFixed(0)}%` : '—', unit: '' },
])

onMounted(async () => {
  await load()
  refreshTimer = window.setInterval(load, 60000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div v-for="k in kpis" :key="k.label" :class="['panel', 'kpi-card', k.brag ? 'brag' : '']">
        <div class="kpi-label">{{ k.label }}</div>
        <div class="kpi-value glow-text">
          {{ k.value }}<span class="unit">{{ k.unit }}</span>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel area-map">
        <div class="panel-title">香港项目分布</div>
        <div class="placeholder">[ 香港地图 · ECharts geoJSON 占位 — Phase 3 接入 ]</div>
      </div>
      <div class="panel area-c-split">
        <div class="panel-title">创造价值构成（口径 C）</div>
        <div class="split-rows">
          <div class="split-row">
            <span class="split-label">相比传统外包 · 累计节省</span>
            <span class="split-value">HK$ {{ fmt10k(cSavings) }} 万</span>
          </div>
          <div class="split-row">
            <span class="split-label">无收入项目 · 创造价值</span>
            <span class="split-value">HK$ {{ fmt10k(cValue) }} 万</span>
          </div>
          <div class="split-row total">
            <span class="split-label">合计</span>
            <span class="split-value brag-num">HK$ {{ fmt10k(cTotal) }} 万</span>
          </div>
          <div class="split-meta">
            来自 {{ sav?.revenue_project_count ?? 0 }} 个有收入项目 +
            {{ sav?.no_revenue_project_count ?? 0 }} 个无收入项目
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  height: 140px;
}
.kpi-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}
.kpi-card.brag {
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 24px rgba(255, 64, 129, 0.35);
}
.kpi-card.brag .kpi-value {
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3), 0 0 16px rgba(255, 64, 129, 0.5);
}
.unit {
  font-size: 0.4em;
  margin-left: 8px;
  color: var(--cockpit-text-dim);
  font-weight: normal;
}
.lower {
  flex: 1;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  min-height: 0;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100% - 30px);
  color: var(--cockpit-text-dim);
  letter-spacing: 2px;
  font-size: 14px;
  border: 1px dashed var(--cockpit-border);
  border-radius: 2px;
}
.split-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}
.split-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 229, 255, 0.15);
}
.split-row.total {
  border-bottom: none;
  border-top: 2px solid var(--cockpit-accent);
  padding-top: 16px;
  margin-top: 4px;
}
.split-label {
  font-size: 15px;
  color: var(--cockpit-text-dim);
  letter-spacing: 2px;
}
.split-value {
  font-family: 'Courier New', monospace;
  font-size: 22px;
  color: var(--cockpit-accent);
  font-weight: 600;
}
.brag-num {
  font-size: 28px;
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3);
}
.split-meta {
  margin-top: 12px;
  text-align: right;
  font-size: 12px;
  color: var(--cockpit-text-dim);
  letter-spacing: 1px;
}
</style>
