<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getRelationshipStats, type RelationshipStats } from '@/api/cockpit'

const data = ref<RelationshipStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getRelationshipStats() } catch { /* keep */ } }

const avgScore = computed(() => data.value?.average_satisfaction ?? 0)
const closurePct = computed(() => Math.round((data.value?.action_closure_rate ?? 0) * 100))
const retroCount = computed(() => data.value?.total_retrospectives ?? 0)
const closedCount = computed(() => data.value?.closed_retrospectives ?? 0)
const maxSat = computed(() =>
  Math.max(1, ...(data.value?.top_clients_by_satisfaction || []).map((c) => c.avg_satisfaction)),
)

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <!-- KPI 行：仅工程师交付质量直接相关 -->
    <div class="kpi-row">
      <div class="panel kpi-card brag">
        <div class="kpi-label">平均满意度</div>
        <div class="rating">
          <div class="stars">
            <span v-for="i in 5" :key="i" class="star"
                  :class="i <= Math.round(avgScore) ? 'on' : ''">★</span>
          </div>
          <div class="rating-num"><CountNumber :value="avgScore" :decimals="1" />/5.0</div>
        </div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">行动项闭环率</div>
        <div class="big-pct"><CountNumber :value="closurePct" /><span class="unit-small">%</span></div>
        <div class="kpi-sub">说要改的事，改了没</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">已完成复盘</div>
        <div class="big-pct"><CountNumber :value="retroCount" /></div>
        <div class="kpi-sub">交付后回顾会数</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">已闭环复盘</div>
        <div class="big-pct"><CountNumber :value="closedCount" /></div>
        <div class="kpi-sub">行动项已落地的</div>
      </div>
    </div>

    <!-- 下半区：客户满意度排行 -->
    <div class="lower-single">
      <div class="panel">
        <div class="panel-title">客户满意度排行（按复盘均分）</div>
        <div v-if="!data?.top_clients_by_satisfaction.length" class="empty">暂无复盘数据</div>
        <div v-else class="bar-list">
          <div v-for="(c, i) in data.top_clients_by_satisfaction" :key="c.need_party_id" class="bar-row">
            <span class="rank-no" :class="`rank-${i+1}`">{{ String(i+1).padStart(2,'0') }}</span>
            <div class="bar-label">{{ c.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${(c.avg_satisfaction / maxSat) * 100}%` }" />
            </div>
            <div class="bar-num">{{ c.avg_satisfaction.toFixed(1) }} ★</div>
            <div class="bar-meta">{{ c.retro_count }} 次复盘</div>
          </div>
        </div>
        <div class="hint-meta">
          客户能否留存由销售、价格、客户内部决策共同决定，本驾驶舱不归因工程师团队，
          故只展示「项目复盘」内可由工程师交付质量影响的部分。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 160px; }
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 12px; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }

.rating { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stars { display: flex; gap: 2px; }
.star { font-size: 28px; color: rgba(255, 224, 130, .2); }
.star.on { color: #ffe082; text-shadow: 0 0 8px #ffe082; }
.rating-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent-3); font-size: 18px; font-weight: 700; }

.big-pct {
  font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700;
  color: var(--cockpit-accent); text-shadow: 0 0 8px var(--cockpit-accent);
  margin-top: 4px;
}
.kpi-sub { color: var(--cockpit-text-dim); font-size: 11px; margin-top: 4px; }
.unit-small { font-size: 0.5em; margin-left: 4px; color: var(--cockpit-text-dim); font-weight: normal; }

.lower-single { flex: 1; min-height: 0; }
.empty { display: flex; align-items: center; justify-content: center; height: calc(100% - 30px); color: var(--cockpit-text-dim); }

.bar-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 40px 220px 1fr 80px 80px; gap: 10px; align-items: center; }
.rank-no { font-family: 'Courier New', monospace; font-weight: 700; text-align: center; color: var(--cockpit-text-dim); }
.rank-1 { color: #ffe082; }
.rank-2 { color: #cfe3ff; }
.rank-3 { color: #ff8e00; }
.bar-label { color: var(--cockpit-text); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { height: 12px; background: rgba(0,229,255,.08); border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2)); box-shadow: 0 0 6px var(--cockpit-accent); }
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; font-size: 13px; }
.bar-meta { color: var(--cockpit-text-dim); font-size: 11px; text-align: right; }

.hint-meta { margin-top: 16px; color: var(--cockpit-text-dim); font-size: 12px; letter-spacing: 1px; line-height: 1.6; }
</style>
