<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
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

// C-tier number split for the brag tile
const cTotal = computed(() => (sav.value?.total_c_view ?? 0) / 10000)
const cSavings = computed(() => (sav.value?.savings_from_revenue_projects ?? 0) / 10000)
const cValue = computed(() => (sav.value?.value_created_from_no_revenue_projects ?? 0) / 10000)
const activeProjects = computed(() => overview.value?.active_projects ?? 0)
const teamSize = computed(() => overview.value?.team_size ?? 0)
const onTimePct = computed(() => Math.round((overview.value?.on_time_delivery_rate ?? 0) * 100))

onMounted(async () => {
  await load()
  refreshTimer = window.setInterval(load, 60000)
})
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card">
        <div class="kpi-label">在管项目</div>
        <div class="kpi-value glow-text"><CountNumber :value="activeProjects" /></div>
      </div>
      <div class="panel kpi-card brag">
        <div class="kpi-label">为公司创造的价值</div>
        <div class="kpi-value glow-text">
          <CountNumber :value="cTotal" :decimals="1" /><span class="unit">万 HKD</span>
        </div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">团队规模</div>
        <div class="kpi-value glow-text"><CountNumber :value="teamSize" /></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">按时交付率</div>
        <div class="kpi-value glow-text">
          <CountNumber :value="onTimePct" /><span class="unit">%</span>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel area-c-split">
        <div class="panel-title">创造价值构成（口径 C）</div>
        <div class="split-rows">
          <div class="split-row">
            <span class="split-label">相比传统外包 · 累计节省</span>
            <span class="split-value">HK$ <CountNumber :value="cSavings" :decimals="1" /> 万</span>
          </div>
          <div class="split-row">
            <span class="split-label">无收入项目 · 创造价值</span>
            <span class="split-value">HK$ <CountNumber :value="cValue" :decimals="1" /> 万</span>
          </div>
          <div class="split-row total">
            <span class="split-label">合计</span>
            <span class="split-value brag-num">HK$ <CountNumber :value="cTotal" :decimals="1" /> 万</span>
          </div>
          <div class="split-meta">
            来自 {{ sav?.revenue_project_count ?? 0 }} 个有收入项目 +
            {{ sav?.no_revenue_project_count ?? 0 }} 个无收入项目
          </div>
        </div>
      </div>
      <div class="panel area-map">
        <div class="panel-title">数据健康</div>
        <div class="health-block">
          <div class="health-row">
            <span class="dot ok"></span>
            <span>驾驶舱数据 60 秒自动刷新</span>
          </div>
          <div class="health-row">
            <span class="dot ok"></span>
            <span>口径隔离 CI 守门：A/B 数字永远不会出现在驾驶舱</span>
          </div>
          <div class="health-row">
            <span class="dot ok"></span>
            <span>三层成本透视：电信付 · Vendor 真实 · 传统外包对标</span>
          </div>
          <div class="health-meta">
            最后更新：{{ overview?.updated_at?.slice(0, 16).replace('T', ' ') || '—' }}
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
.health-block {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 16px;
  height: calc(100% - 30px);
}
.health-row {
  display: flex; align-items: center; gap: 12px;
  color: var(--cockpit-text); font-size: 14px;
  padding: 10px;
  border: 1px solid var(--cockpit-border);
  background: rgba(0, 229, 255, 0.04);
}
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #67ff8a;
  box-shadow: 0 0 8px #67ff8a;
  animation: dot-pulse 2s ease-in-out infinite;
}
@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.4; }
}
.health-meta {
  margin-top: auto;
  text-align: right;
  color: var(--cockpit-text-dim);
  font-size: 12px;
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
