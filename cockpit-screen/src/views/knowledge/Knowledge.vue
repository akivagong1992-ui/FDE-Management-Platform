<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getKnowledgeStats, type KnowledgeStats } from '@/api/cockpit'

const stats = ref<KnowledgeStats | null>(null)
let timer: number | undefined

async function load() {
  try { stats.value = await getKnowledgeStats() } catch { /* keep last snapshot */ }
}

function fmtInt(n: number | undefined | null): string {
  return n == null ? '—' : Math.round(n).toLocaleString('en-HK')
}

const total = computed(() => stats.value?.total_assets ?? 0)
const refCount = computed(() => stats.value?.total_references ?? 0)
const distinctReused = computed(() => stats.value?.distinct_reused_assets ?? 0)
const hoursSaved = computed(() => stats.value?.total_hours_saved ?? 0)
const coverage = computed(() => stats.value?.project_coverage ?? 0)

const maxCount = computed(() => Math.max(1, ...(stats.value?.by_category || []).map((c) => c.count)))

onMounted(async () => {
  await load()
  timer = window.setInterval(load, 60000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card brag">
        <div class="kpi-label">累计知识资产</div>
        <div class="kpi-value glow-text"><CountNumber :value="total" /></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">跨项目复用次数</div>
        <div class="kpi-value glow-text"><CountNumber :value="refCount" /></div>
        <div class="kpi-sub"><CountNumber :value="distinctReused" /> 个资产被复用</div>
      </div>
      <div class="panel kpi-card brag-2">
        <div class="kpi-label">复用节省工时</div>
        <div class="kpi-value glow-text"><CountNumber :value="hoursSaved" /><span class="unit"> 工时</span></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">沉淀过的项目数</div>
        <div class="kpi-value glow-text"><CountNumber :value="coverage" /></div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">按分类分布</div>
        <div v-if="!stats || stats.by_category.length === 0" class="placeholder">暂无数据</div>
        <div v-else class="bar-list">
          <div v-for="c in stats.by_category" :key="c.code" class="bar-row">
            <div class="bar-label">{{ c.label }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${(c.count / maxCount) * 100}%` }" />
            </div>
            <div class="bar-num">{{ c.count }}</div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">直击痛点</div>
        <div class="hint-block">
          <div class="hint-title">无技术沉淀 → 沉淀在内部</div>
          <div class="hint-body">
            过去项目结束 = 知识丢失。<br />
            内化后已累计 <strong class="hl">{{ fmtInt(stats?.total_assets) }}</strong>
            条资产，覆盖 <strong class="hl">{{ fmtInt(stats?.project_coverage) }}</strong> 个项目。
          </div>
          <div class="hint-meta">数据来源：管理后台 ⑥ 技术沉淀模块</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px; }
.kpi-card {
  display: flex; flex-direction: column; justify-content: center;
  align-items: center; text-align: center;
}
.kpi-card.brag {
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 24px rgba(255, 64, 129, 0.35);
}
.kpi-card.brag .kpi-value {
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3), 0 0 16px rgba(255, 64, 129, 0.5);
}
.kpi-card.brag-2 {
  border-color: #ffe082;
  box-shadow: 0 0 18px rgba(255, 224, 130, 0.3);
}
.kpi-card.brag-2 .kpi-value { color: #ffe082; text-shadow: 0 0 8px #ffe082; }
.unit { font-size: 0.4em; color: var(--cockpit-text-dim); font-weight: normal; }
.kpi-sub { color: var(--cockpit-text-dim); font-size: 11px; margin-top: 4px; }
.lower { flex: 1; display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; min-height: 0; }
.placeholder {
  display: flex; align-items: center; justify-content: center;
  height: calc(100% - 30px); color: var(--cockpit-text-dim); letter-spacing: 2px;
}

.bar-list { display: flex; flex-direction: column; gap: 14px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 120px 1fr 60px; gap: 12px; align-items: center; }
.bar-label { color: var(--cockpit-text); font-size: 14px; }
.bar-track {
  height: 14px; background: rgba(0, 229, 255, 0.08);
  border: 1px solid var(--cockpit-border); border-radius: 2px; overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 8px var(--cockpit-accent);
  transition: width 0.6s ease;
}
.bar-num {
  font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600;
  text-align: right;
}

.hint-block { padding: 16px 8px; }
.hint-title {
  font-size: 18px; color: var(--cockpit-accent-3); letter-spacing: 3px;
  margin-bottom: 16px; text-shadow: 0 0 6px var(--cockpit-accent-3);
}
.hint-body { font-size: 15px; line-height: 1.9; color: var(--cockpit-text); }
.hl {
  color: var(--cockpit-accent); font-family: 'Courier New', monospace;
  font-size: 22px; padding: 0 4px;
}
.hint-meta { margin-top: 20px; color: var(--cockpit-text-dim); font-size: 12px; letter-spacing: 1px; }
</style>
