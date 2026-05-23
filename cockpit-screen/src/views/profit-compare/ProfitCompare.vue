<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getProfitCompare, type ProfitCompare } from '@/api/cockpit'

const data = ref<ProfitCompare | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getProfitCompare() } catch { /* keep */ } }

function fmt10k(n: number | undefined | null): string {
  if (n == null) return '—'
  return (n / 10000).toLocaleString('en-HK', { maximumFractionDigits: 1 })
}

const cSavings10k = computed(() => (data.value?.total_savings ?? 0) / 10000)
const cValue10k = computed(() => (data.value?.total_value_created ?? 0) / 10000)
const cTotal10k = computed(() => (data.value?.total_c_view ?? 0) / 10000)

const maxSavings = computed(() => Math.max(1, ...(data.value?.top_savings_projects || []).map((p) => p.savings)))
const maxValue = computed(() => Math.max(1, ...(data.value?.top_value_projects || []).map((p) => p.value_created)))

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card">
        <div class="kpi-label">累计节省（vs 传统外包）</div>
        <div class="kpi-value glow-text"><CountNumber :value="cSavings10k" :decimals="1" /><span class="unit">万 HKD</span></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">无收入项目 · 创造价值</div>
        <div class="kpi-value glow-text"><CountNumber :value="cValue10k" :decimals="1" /><span class="unit">万 HKD</span></div>
      </div>
      <div class="panel kpi-card brag">
        <div class="kpi-label">合计 (口径 C)</div>
        <div class="kpi-value glow-text"><CountNumber :value="cTotal10k" :decimals="1" /><span class="unit">万 HKD</span></div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">Top 节省项目（vs 传统外包）</div>
        <div v-if="!data?.top_savings_projects.length" class="empty">暂无数据</div>
        <div v-else class="bar-list">
          <div v-for="p in data.top_savings_projects" :key="p.project_id" class="bar-row">
            <div class="bar-label">{{ p.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${(p.savings / maxSavings) * 100}%` }" />
            </div>
            <div class="bar-num">HK$ {{ fmt10k(p.savings) }}万</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">Top 创造价值（无收入项目）</div>
        <div v-if="!data?.top_value_projects.length" class="empty">暂无数据</div>
        <div v-else class="bar-list">
          <div v-for="p in data.top_value_projects" :key="p.project_id" class="bar-row">
            <div class="bar-label">{{ p.name }}</div>
            <div class="bar-track">
              <div class="bar-fill brag-fill" :style="{ width: `${(p.value_created / maxValue) * 100}%` }" />
            </div>
            <div class="bar-num brag-text">HK$ {{ fmt10k(p.value_created) }}万</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">Vendor 节省贡献榜</div>
        <div v-if="!data?.vendor_contribution_rank.length" class="empty">需先把 Vendor 服务费挂到项目</div>
        <div v-else class="rank-list">
          <div v-for="(v, i) in data.vendor_contribution_rank" :key="v.vendor_id" class="rank-row">
            <span class="rank-no" :class="`rank-${i+1}`">{{ String(i+1).padStart(2,'0') }}</span>
            <span class="rank-name">{{ v.name }}</span>
            <span class="rank-num">HK$ {{ fmt10k(v.savings) }}万</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; height: 140px; }
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
.kpi-card.brag {
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 24px rgba(255, 64, 129, 0.35);
}
.kpi-card.brag .kpi-value {
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3);
}
.unit { font-size: 0.4em; margin-left: 8px; color: var(--cockpit-text-dim); font-weight: normal; }
.lower { flex: 1; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; min-height: 0; }
.empty {
  display: flex; align-items: center; justify-content: center;
  height: calc(100% - 30px); color: var(--cockpit-text-dim); font-size: 13px;
}

.bar-list { display: flex; flex-direction: column; gap: 14px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 100px 1fr 100px; gap: 8px; align-items: center; }
.bar-label { color: var(--cockpit-text); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track {
  height: 12px; background: rgba(0, 229, 255, 0.08);
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 8px var(--cockpit-accent);
}
.brag-fill {
  background: linear-gradient(90deg, var(--cockpit-accent-3), #ffe082);
  box-shadow: 0 0 8px var(--cockpit-accent-3);
}
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; font-size: 12px; text-align: right; }
.brag-text { color: var(--cockpit-accent-3); }

.rank-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.rank-row { display: grid; grid-template-columns: 50px 1fr 100px; gap: 8px; align-items: center; }
.rank-no {
  font-family: 'Courier New', monospace; font-weight: 700; font-size: 16px;
  text-align: center; color: var(--cockpit-text-dim);
}
.rank-1 { color: #ffe082; }
.rank-2 { color: #cfe3ff; }
.rank-3 { color: #ff8e00; }
.rank-name { color: var(--cockpit-text); }
.rank-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); text-align: right; font-size: 13px; }
</style>
