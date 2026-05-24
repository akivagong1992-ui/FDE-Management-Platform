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

// 最新沉淀滚动播放：超过 4 条就走 CSS 无缝循环（拼一份副本）
const tickerList = computed(() => {
  const list = stats.value?.recent_assets || []
  return list.length > 4 ? [...list, ...list] : list
})
const isScrolling = computed(() => (stats.value?.recent_assets.length || 0) > 4)

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const t = new Date(iso).getTime()
  const diff = Date.now() - t
  const d = Math.floor(diff / 86400000)
  if (d < 1) {
    const h = Math.floor(diff / 3600000)
    return h < 1 ? '刚刚' : `${h} 小时前`
  }
  if (d < 30) return `${d} 天前`
  const m = Math.floor(d / 30)
  return `${m} 个月前`
}

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
        <div class="panel-title">
          最新沉淀
          <span class="panel-sub">
            最近 30 天 <strong class="hl-mini">{{ fmtInt(stats?.recent_30d) }}</strong> 条
          </span>
        </div>
        <div v-if="!stats?.recent_assets.length" class="placeholder">暂无沉淀</div>
        <div v-else class="ticker" :class="{ 'is-scrolling': isScrolling }">
          <div class="ticker-track">
            <div v-for="(a, i) in tickerList" :key="`${a.id}-${i}`" class="ticker-row">
              <div class="ticker-cat">{{ a.category_label }}</div>
              <div class="ticker-main">
                <div class="ticker-title">{{ a.title }}</div>
                <div class="ticker-meta">
                  <span v-if="a.project_name">📁 {{ a.project_name }}</span>
                  <span v-else class="dim">未归属项目</span>
                  <span class="dim">·</span>
                  <span class="dim">{{ timeAgo(a.created_at) }}</span>
                </div>
              </div>
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
  border-color: var(--cockpit-accent-gold);
  box-shadow: 0 0 18px rgba(255, 224, 130, 0.3);
}
.kpi-card.brag-2 .kpi-value { color: var(--cockpit-accent-gold); text-shadow: 0 0 8px var(--cockpit-accent-gold); }
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
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
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

.panel-sub {
  font-size: 11px; color: var(--cockpit-text-dim); letter-spacing: 1px; margin-left: 8px;
  font-weight: normal;
}
.hl-mini { color: var(--cockpit-accent-3); font-family: 'Courier New', monospace; padding: 0 2px; }

.ticker {
  margin-top: 12px; overflow: hidden;
  height: calc(100% - 40px);
  position: relative;
  mask-image: linear-gradient(180deg, transparent 0, #000 12%, #000 88%, transparent 100%);
}
.ticker-track {
  display: flex; flex-direction: column; gap: 10px;
}
.ticker.is-scrolling .ticker-track {
  animation: ticker-scroll 30s linear infinite;
}
@keyframes ticker-scroll {
  0% { transform: translateY(0); }
  100% { transform: translateY(-50%); }
}
.ticker-row {
  display: grid; grid-template-columns: 80px 1fr; gap: 12px;
  align-items: center; padding: 8px 10px;
  border: 1px solid var(--cockpit-border); border-radius: 8px;
  background: rgba(0, 229, 255, 0.04);
}
.ticker-cat {
  color: var(--cockpit-accent); font-size: 11px; letter-spacing: 1px;
  text-align: center; padding: 4px 0;
  border-right: 1px solid var(--cockpit-border);
}
.ticker-main { min-width: 0; }
.ticker-title {
  color: var(--cockpit-text); font-size: 13px; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ticker-meta {
  color: var(--cockpit-text); font-size: 11px; margin-top: 3px;
  display: flex; gap: 6px; align-items: center;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ticker-meta .dim { color: var(--cockpit-text-dim); }
</style>
