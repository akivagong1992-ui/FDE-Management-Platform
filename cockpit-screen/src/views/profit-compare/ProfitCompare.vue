<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getProfitCompare, getMarginLiftPct, type ProfitCompare, type MarginLiftPct } from '@/api/cockpit'

const data = ref<ProfitCompare | null>(null)
const marginLift = ref<MarginLiftPct | null>(null)
let timer: number | undefined

async function load() {
  try { data.value = await getProfitCompare() } catch { /* keep */ }
  try { marginLift.value = await getMarginLiftPct() } catch { /* keep */ }
}

function fmt10k(n: number | undefined | null): string {
  if (n == null) return '—'
  return (n / 10000).toLocaleString('en-HK', { maximumFractionDigits: 1 })
}

const cSavings10k = computed(() => (data.value?.total_savings ?? 0) / 10000)
const cValue10k = computed(() => (data.value?.total_value_created ?? 0) / 10000)

const maxSavings = computed(() => Math.max(1, ...(data.value?.top_savings_projects || []).map((p) => p.savings)))
const maxValue = computed(() => Math.max(1, ...(data.value?.top_value_projects || []).map((p) => p.value_created)))

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card">
        <div class="kpi-label">降本总金额</div>
        <div class="kpi-value glow-text"><CountNumber :value="cSavings10k" :decimals="1" /><span class="unit">万 HKD</span></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">增效总金额</div>
        <div class="kpi-value glow-text"><CountNumber :value="cValue10k" :decimals="1" /><span class="unit">万 HKD</span></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">老外包毛利率</div>
        <div class="kpi-value glow-text"><CountNumber :value="marginLift?.outsource_margin_pct ?? 0" :decimals="2" /><span class="unit">%</span></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">FDE 模式毛利率</div>
        <div class="kpi-value glow-text"><CountNumber :value="marginLift?.fde_margin_pct ?? 0" :decimals="2" /><span class="unit">%</span></div>
      </div>
      <div class="panel kpi-card brag">
        <div class="kpi-label">项目利润变化</div>
        <div class="kpi-value glow-text">+<CountNumber :value="marginLift?.margin_lift_pct ?? 0" :decimals="2" /><span class="unit">个百分点</span></div>
        <div class="kpi-sub">基于 {{ marginLift?.counted_projects ?? 0 }} 个已中标项目</div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">Top 降本项目（vs 服务商分包模式）</div>
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
        <div class="panel-title">Top 增效项目</div>
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
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; height: 140px; }
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
.lower { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 0; }
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
  background: linear-gradient(90deg, var(--cockpit-accent-3), var(--cockpit-accent-gold));
  box-shadow: 0 0 8px var(--cockpit-accent-3);
}
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; font-size: 12px; text-align: right; }
.brag-text { color: var(--cockpit-accent-3); }

/* 项目利润变化 brag 卡的副文案 */
.kpi-sub {
  margin-top: 8px;
  color: var(--cockpit-text-dim); font-size: 12px;
  font-family: 'Courier New', monospace;
}
</style>
