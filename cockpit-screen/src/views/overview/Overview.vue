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

const cTotal = computed(() => (sav.value?.total_c_view ?? 0) / 10000)
const activeProjects = computed(() => overview.value?.active_projects ?? 0)
const teamSize = computed(() => overview.value?.team_size ?? 0)
const onTimePct = computed(() => Math.round((overview.value?.on_time_delivery_rate ?? 0) * 100))
const deliveredClients = computed(() => overview.value?.delivered_clients ?? [])
const capabilities = computed(() => overview.value?.capability_by_category ?? [])
const maxCap = computed(() => Math.max(1, ...capabilities.value.map((c) => c.engineer_count)))

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
        <div class="kpi-label">降本金额</div>
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
      <!-- 能力矩阵卡 -->
      <div class="panel">
        <div class="panel-title">能力矩阵</div>
        <div v-if="capabilities.length === 0" class="empty">暂无技能登记</div>
        <div v-else class="cap-grid">
          <div v-for="c in capabilities" :key="c.category" class="cap-cell">
            <div class="cap-name">{{ c.category }}</div>
            <div class="cap-bar">
              <div class="cap-fill" :style="{ width: `${(c.engineer_count / maxCap) * 100}%` }" />
            </div>
            <div class="cap-num">
              <CountNumber :value="c.engineer_count" /> 人
            </div>
          </div>
        </div>
        <div class="cap-meta" v-if="capabilities.length > 0">
          覆盖 <strong class="hi">{{ capabilities.length }}</strong> 个技能领域
          / 团队总规模 <strong class="hi">{{ teamSize }}</strong> 人
        </div>
      </div>

      <!-- 已交付客户卡 -->
      <div class="panel">
        <div class="panel-title">已交付客户（{{ deliveredClients.length }}）</div>
        <div v-if="deliveredClients.length === 0" class="empty">暂无已验收/已归档项目</div>
        <div v-else class="client-grid">
          <div v-for="(name, i) in deliveredClients" :key="i" class="client-chip">
            <span class="chip-dot"></span>
            <span class="chip-name">{{ name }}</span>
          </div>
        </div>
        <div class="cap-meta" v-if="deliveredClients.length > 0">
          数据口径：拥有验收/归档项目的客户
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: flex; flex-direction: column; height: 100%; gap: 16px;
}
.kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px;
}
.kpi-card {
  display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
}
.kpi-card.brag {
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 24px rgba(255, 64, 129, 0.35);
}
.kpi-card.brag .kpi-value {
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3), 0 0 16px rgba(255, 64, 129, 0.5);
}
.unit { font-size: 0.4em; margin-left: 8px; color: var(--cockpit-text-dim); font-weight: normal; }

.lower {
  flex: 1; display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; min-height: 0;
}
.empty {
  display: flex; align-items: center; justify-content: center;
  height: calc(100% - 30px); color: var(--cockpit-text-dim);
}

/* 能力矩阵 */
.cap-grid {
  display: flex; flex-direction: column; gap: 10px; margin-top: 12px;
}
.cap-cell {
  display: grid; grid-template-columns: 90px 1fr 70px; gap: 12px; align-items: center;
}
.cap-name { color: var(--cockpit-text); font-size: 14px; }
.cap-bar {
  height: 14px; background: rgba(0, 229, 255, 0.08);
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
}
.cap-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 8px var(--cockpit-accent);
  transition: width 0.6s ease;
}
.cap-num {
  font-family: 'Courier New', monospace;
  color: var(--cockpit-accent); font-weight: 600;
  text-align: right;
}
.cap-meta {
  margin-top: 16px;
  color: var(--cockpit-text-dim);
  font-size: 12px;
  letter-spacing: 1px;
}
.hi { color: var(--cockpit-accent); font-family: 'Courier New', monospace; padding: 0 2px; }

/* 已交付客户 */
.client-grid {
  display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px;
  align-content: flex-start;
}
.client-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 229, 255, 0.08);
  border: 1px solid var(--cockpit-border);
  border-radius: 10px;
  font-size: 13px;
  color: var(--cockpit-text);
  transition: all 0.3s;
}
.client-chip:hover {
  background: rgba(255, 64, 129, 0.12);
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 8px rgba(255, 64, 129, 0.3);
}
.chip-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--cockpit-accent);
  box-shadow: 0 0 4px var(--cockpit-accent);
}
.chip-name { letter-spacing: 1px; }
</style>
