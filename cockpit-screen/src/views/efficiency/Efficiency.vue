<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getEfficiencyStats, type EfficiencyStats } from '@/api/cockpit'

const data = ref<EfficiencyStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getEfficiencyStats() } catch { /* keep */ } }

// 状态漏斗顺序：立项 → 进行中 → 验收 → 收尾 → 归档
const FUNNEL_ORDER = ['drafting', 'in_progress', 'accepting', 'closing', 'archived']
const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收', closing: '收尾', archived: '归档',
}

const funnel = computed(() => {
  const map = new Map((data.value?.by_status || []).map((s) => [s.label, s.count]))
  return FUNNEL_ORDER.map((s) => ({ status: s, label: STATUS_LABEL[s] || s, count: map.get(s) || 0 }))
})
const funnelMax = computed(() => Math.max(1, ...funnel.value.map((f) => f.count)))

// 在管项目进度条：按 status 投射百分比
// 现实里 planned 起止日期常常是猜的（不准），状态才是更可靠的信号 → 改成状态驱动
const STATUS_PCT: Record<string, number> = {
  drafting: 0,
  in_progress: 50,
  accepting: 80,
  closing: 95,
  archived: 100,
  cancelled: 0,
}
function progressPct(p: { status: string }): number {
  return STATUS_PCT[p.status] ?? 0
}

function daysToDueLabel(n: number): string {
  if (n < 0) return `逾期 ${-n} 天`
  if (n === 0) return '今天到期'
  return `还有 ${n} 天`
}

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <!-- KPI 行：全部纯计数，不含率 -->
    <div class="kpi-row">
      <div class="panel kpi-card">
        <div class="kpi-label">在管项目</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.active_count ?? 0" /></div>
        <div class="kpi-sub">含立项 / 进行中 / 验收</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">本月完成</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.completed_this_month ?? 0" /></div>
        <div class="kpi-sub">actual_end 落在本月</div>
      </div>
      <div class="panel kpi-card brag">
        <div class="kpi-label">14 天内到期</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.due_soon_count ?? 0" /></div>
        <div class="kpi-sub">含已逾期</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">累计已交付</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.delivered_total ?? 0" /></div>
        <div class="kpi-sub">收尾 + 归档</div>
      </div>
    </div>

    <div class="lower">
      <!-- 状态漏斗 -->
      <div class="panel">
        <div class="panel-title">项目状态漏斗</div>
        <div class="funnel">
          <div v-for="f in funnel" :key="f.status" class="funnel-row">
            <div class="funnel-name">{{ f.label }}</div>
            <div class="funnel-bar">
              <div class="funnel-fill" :style="{ width: `${(f.count / funnelMax) * 100}%` }" />
            </div>
            <div class="funnel-num"><CountNumber :value="f.count" /></div>
          </div>
        </div>

        <div class="panel-title" style="margin-top: 24px">14 天内到期</div>
        <div v-if="!data?.due_soon.length" class="empty-mini">无即将到期项目</div>
        <div v-else class="due-list">
          <div v-for="p in data.due_soon.slice(0, 6)" :key="p.project_id" class="due-row">
            <span class="due-name">{{ p.name }}</span>
            <span :class="['due-tag', p.overdue ? 'late' : 'on']">{{ daysToDueLabel(p.days_to_due) }}</span>
          </div>
        </div>
      </div>

      <!-- 在管项目进度表 -->
      <div class="panel">
        <div class="panel-title">在管项目进度（{{ data?.in_progress_projects.length ?? 0 }}）</div>
        <div v-if="!data?.in_progress_projects.length" class="empty">暂无在管项目</div>
        <div v-else class="progress-list">
          <div v-for="p in data.in_progress_projects" :key="p.project_id" class="progress-row">
            <div class="prog-name-row">
              <span class="prog-name">{{ p.name }}</span>
              <span class="prog-status">{{ STATUS_LABEL[p.status] || p.status }}</span>
              <span v-if="p.overdue" class="prog-overdue">⚠ 已逾期</span>
            </div>
            <div class="prog-bar">
              <div class="prog-fill" :class="{ over: p.overdue }" :style="{ width: `${progressPct(p)}%` }" />
            </div>
            <div class="prog-meta">
              <span>计划 {{ p.planned_start || '—' }} → {{ p.planned_end || '—' }}</span>
              <span class="prog-pct">{{ progressPct(p) }}%</span>
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
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 10px; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }
.kpi-card.brag .kpi-value { color: var(--cockpit-accent-3); text-shadow: 0 0 8px var(--cockpit-accent-3); }
.kpi-sub { color: var(--cockpit-text-dim); font-size: 11px; margin-top: 4px; }

.lower { flex: 1; display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; min-height: 0; }
.empty { display: flex; align-items: center; justify-content: center; height: calc(100% - 30px); color: var(--cockpit-text-dim); }
.empty-mini { color: var(--cockpit-text-dim); font-size: 12px; margin-top: 8px; }

/* 状态漏斗 */
.funnel { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.funnel-row { display: grid; grid-template-columns: 70px 1fr 50px; gap: 12px; align-items: center; }
.funnel-name { color: var(--cockpit-text); font-size: 13px; }
.funnel-bar {
  height: 16px; background: rgba(0,229,255,.08);
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
}
.funnel-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 8px var(--cockpit-accent);
  transition: width 0.6s ease;
}
.funnel-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; }

/* 到期列表 */
.due-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.due-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 12px; }
.due-name { color: var(--cockpit-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.due-tag { font-family: 'Courier New', monospace; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
.due-tag.on { background: rgba(0,229,255,.15); color: var(--cockpit-accent); }
.due-tag.late { background: rgba(255,64,129,.2); color: var(--cockpit-accent-3); }

/* 在管项目进度表 */
.progress-list {
  display: flex; flex-direction: column; gap: 14px; margin-top: 12px;
  overflow-y: auto; max-height: 100%; padding-right: 4px;
}
.progress-row {
  background: rgba(10, 25, 41, 0.4);
  border: 1px solid var(--cockpit-border);
  border-radius: 10px; padding: 10px 12px;
}
.prog-name-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.prog-name { color: var(--cockpit-text); font-size: 13px; font-weight: 600; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.prog-status {
  font-family: 'Courier New', monospace; font-size: 11px;
  padding: 2px 8px; border-radius: 999px;
  background: rgba(0,229,255,.12); color: var(--cockpit-accent);
}
.prog-overdue { font-size: 11px; color: var(--cockpit-accent-3); font-weight: 600; }
.prog-bar {
  height: 8px; background: rgba(0,229,255,.08);
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
}
.prog-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 6px var(--cockpit-accent);
  transition: width 0.6s ease;
}
.prog-fill.over {
  background: linear-gradient(90deg, var(--cockpit-accent-3), #ff8e00);
  box-shadow: 0 0 6px var(--cockpit-accent-3);
}
.prog-meta {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 6px; font-size: 11px; color: var(--cockpit-text-dim);
  font-family: 'Courier New', monospace;
}
.prog-pct { color: var(--cockpit-accent); font-weight: 600; }
</style>
