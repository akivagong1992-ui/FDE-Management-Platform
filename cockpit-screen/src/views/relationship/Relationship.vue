<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getRelationshipStats, type RelationshipStats } from '@/api/cockpit'

const data = ref<RelationshipStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getRelationshipStats() } catch { /* keep */ } }

const avgScore = computed(() => data.value?.average_satisfaction ?? 0)
const renewalPct = computed(() => Math.round((data.value?.renewal_rate_proxy ?? 0) * 100))
const closurePct = computed(() => Math.round((data.value?.action_closure_rate ?? 0) * 100))
const winRatePct = computed(() => Math.round((data.value?.renewal_win_rate ?? 0) * 100))
const wonCount = computed(() => data.value?.renewal_won_count ?? 0)
const lostCount = computed(() => data.value?.renewal_lost_count ?? 0)
const pendingCount = computed(() => data.value?.renewal_pending_count ?? 0)
const totalAttempts = computed(() => data.value?.renewal_attempts_total ?? 0)
const retrospectivesCount = computed(() => data.value?.total_retrospectives ?? 0)
const maxClientProj = computed(() => Math.max(1, ...(data.value?.top_clients_by_project_count || []).map((c) => c.project_count)))
const maxReason = computed(() => Math.max(1, ...(data.value?.renewal_lost_reasons || []).map((r) => r.count)))

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
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
      <div class="panel kpi-card brag-2">
        <div class="kpi-label">续单胜率</div>
        <div class="big-pct"><CountNumber :value="winRatePct" /><span class="unit-small">%</span></div>
        <div class="kpi-sub">
          <span class="ok"><CountNumber :value="wonCount" />赢</span>
          /
          <span class="ng"><CountNumber :value="lostCount" />输</span>
          /
          <span class="dim"><CountNumber :value="pendingCount" />洽谈</span>
        </div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">行动项闭环率</div>
        <div class="big-pct"><CountNumber :value="closurePct" /><span class="unit-small">%</span></div>
        <div class="kpi-sub"><CountNumber :value="retrospectivesCount" /> 条复盘</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">续单跟踪总数</div>
        <div class="big-pct"><CountNumber :value="totalAttempts" /></div>
        <div class="kpi-sub">显式登记的续单尝试</div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">Top 客户（按累计项目数）</div>
        <div v-if="!data?.top_clients_by_project_count.length" class="empty">暂无客户数据</div>
        <div v-else class="bar-list">
          <div v-for="(c, i) in data.top_clients_by_project_count" :key="c.need_party_id" class="bar-row">
            <span class="rank-no" :class="`rank-${i+1}`">{{ String(i+1).padStart(2,'0') }}</span>
            <div class="bar-label">{{ c.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${(c.project_count / maxClientProj) * 100}%` }" />
            </div>
            <div class="bar-num">{{ c.project_count }} 个</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">续单输因分布</div>
        <div v-if="!data?.renewal_lost_reasons?.length" class="empty">暂无输单记录</div>
        <div v-else class="bar-list">
          <div v-for="r in data.renewal_lost_reasons" :key="r.code" class="bar-row reason-row">
            <div class="bar-label">{{ r.label }}</div>
            <div class="bar-track">
              <div class="bar-fill lost-fill" :style="{ width: `${(r.count / maxReason) * 100}%` }" />
            </div>
            <div class="bar-num lost-num">{{ r.count }}</div>
          </div>
        </div>
        <div class="hint-meta" v-if="data?.renewal_lost_reasons?.length">
          管理后台 ⑧ 需求方关系 → 续单跟踪 维护
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
.kpi-card.brag-2 { border-color: #ffe082; box-shadow: 0 0 18px rgba(255, 224, 130, 0.3); }
.kpi-card.brag-2 .big-pct { color: #ffe082; text-shadow: 0 0 8px #ffe082; }

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

.sat-bar { width: 80%; height: 12px; background: rgba(0,229,255,.1); border: 1px solid var(--cockpit-border); margin-top: 8px; border-radius: 2px; overflow: hidden; }
.sat-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent-3), #ffe082); box-shadow: 0 0 6px var(--cockpit-accent-3); transition: width .6s ease; }

.lower { flex: 1; display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; min-height: 0; }
.empty { display: flex; align-items: center; justify-content: center; height: calc(100% - 30px); color: var(--cockpit-text-dim); }

.bar-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 40px 140px 1fr 70px; gap: 8px; align-items: center; }
.rank-no { font-family: 'Courier New', monospace; font-weight: 700; text-align: center; color: var(--cockpit-text-dim); }
.rank-1 { color: #ffe082; }
.rank-2 { color: #cfe3ff; }
.rank-3 { color: #ff8e00; }
.bar-label { color: var(--cockpit-text); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { height: 12px; background: rgba(0,229,255,.08); border: 1px solid var(--cockpit-border); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2)); box-shadow: 0 0 6px var(--cockpit-accent); }
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; font-size: 12px; }
.reason-row { grid-template-columns: 140px 1fr 50px; }
.lost-fill { background: linear-gradient(90deg, var(--cockpit-accent-3), #ff8e00); box-shadow: 0 0 6px var(--cockpit-accent-3); }
.lost-num { color: var(--cockpit-accent-3); }
.unit-small { font-size: 0.5em; margin-left: 4px; color: var(--cockpit-text-dim); font-weight: normal; }
.ok { color: #67ff8a; font-family: 'Courier New', monospace; font-weight: 600; }
.ng { color: var(--cockpit-accent-3); font-family: 'Courier New', monospace; font-weight: 600; }
.dim { color: var(--cockpit-text-dim); font-family: 'Courier New', monospace; }

.hint-block { padding: 16px 8px; }
.hint-title { font-size: 18px; color: var(--cockpit-accent-3); letter-spacing: 3px; margin-bottom: 16px; text-shadow: 0 0 6px var(--cockpit-accent-3); }
.hint-body { font-size: 15px; line-height: 1.9; color: var(--cockpit-text); }
.hl { color: var(--cockpit-accent); font-family: 'Courier New', monospace; font-size: 22px; padding: 0 4px; }
.hint-meta { margin-top: 20px; color: var(--cockpit-text-dim); font-size: 12px; letter-spacing: 1px; }
</style>
