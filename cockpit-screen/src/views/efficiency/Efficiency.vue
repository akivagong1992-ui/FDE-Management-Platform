<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import CountNumber from '@/components/CountNumber.vue'
import { getEfficiencyStats, type EfficiencyStats } from '@/api/cockpit'

const data = ref<EfficiencyStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getEfficiencyStats() } catch { /* keep */ } }

const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收', closing: '收尾', archived: '归档',
}

const onTimePct = computed(() => {
  const r = data.value?.on_time_rate ?? 0
  return Math.round(r * 100)
})

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card brag">
        <div class="kpi-label">按时交付率</div>
        <div class="gauge">
          <svg viewBox="0 0 120 120" style="width: 110px; height: 110px">
            <circle cx="60" cy="60" r="50" stroke="rgba(0,229,255,.15)" stroke-width="10" fill="none" />
            <circle cx="60" cy="60" r="50" stroke="#ff4081" stroke-width="10" fill="none"
                    :stroke-dasharray="`${onTimePct * 3.14} ${314 - onTimePct * 3.14}`"
                    stroke-dashoffset="-78.5" stroke-linecap="round" />
            <text x="60" y="68" text-anchor="middle" fill="#ff4081"
                  font-size="28" font-weight="700" font-family="Courier New">
              {{ onTimePct }}%
            </text>
          </svg>
        </div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">零失误交付（无返工 ≤1变更）</div>
        <div class="kpi-value glow-text"><CountNumber :value="data?.clean_delivery_count ?? 0" /></div>
        <div class="kpi-sub">已归档项目中</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">返工率</div>
        <div class="big-pct"><CountNumber :value="(data?.rework_rate ?? 0) * 100" />%</div>
        <div class="kpi-sub">累计返工 <CountNumber :value="data?.total_rework_count ?? 0" /> 次</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">人均变更次数</div>
        <div class="big-pct"><CountNumber :value="data?.avg_changes_per_project ?? 0" :decimals="2" /></div>
        <div class="kpi-sub">累计 <CountNumber :value="data?.total_change_count ?? 0" /> 次变更</div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">项目状态分布</div>
        <div class="status-grid">
          <div v-for="s in data?.by_status || []" :key="s.label" class="status-pill">
            <div class="status-label">{{ STATUS_LABEL[s.label] || s.label }}</div>
            <div class="status-count">{{ s.count }}</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">最近完成项目</div>
        <div v-if="!data?.recent_completions.length" class="empty">尚无完成项目</div>
        <div v-else class="recent-list">
          <div v-for="p in data.recent_completions" :key="p.project_id" class="recent-row">
            <div class="recent-name">{{ p.name }}</div>
            <div class="recent-meta">
              <span class="recent-date">完成：{{ p.actual_end }}</span>
              <span class="recent-date">计划：{{ p.planned_end || '—' }}</span>
              <span :class="['recent-tag', p.on_time ? 'on' : 'late']">
                {{ p.on_time ? '✓ 按时' : '✗ 延期' }}
              </span>
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
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }
.big-pct {
  font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700;
  color: var(--cockpit-accent); text-shadow: 0 0 8px var(--cockpit-accent);
}
.kpi-sub { color: var(--cockpit-text-dim); font-size: 11px; margin-top: 4px; }
.gauge { margin-top: 4px; }
.lower { flex: 1; display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; min-height: 0; }
.empty { display: flex; align-items: center; justify-content: center; height: calc(100% - 30px); color: var(--cockpit-text-dim); }

.status-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
.status-pill {
  padding: 16px; border: 1px solid var(--cockpit-border); border-radius: 2px;
  background: rgba(10, 25, 41, 0.6); text-align: center;
}
.status-label { color: var(--cockpit-text-dim); font-size: 12px; letter-spacing: 2px; }
.status-count { font-family: 'Courier New', monospace; font-size: 24px; font-weight: 700; color: var(--cockpit-accent); margin-top: 6px; }

.recent-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.recent-row {
  padding: 10px; border-left: 3px solid var(--cockpit-accent);
  background: rgba(10, 25, 41, 0.5);
}
.recent-name { color: var(--cockpit-text); font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.recent-meta { display: flex; gap: 12px; align-items: center; }
.recent-date { color: var(--cockpit-text-dim); font-size: 11px; font-family: 'Courier New', monospace; }
.recent-tag { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 2px; }
.recent-tag.on { background: rgba(0,229,255,.2); color: var(--cockpit-accent); }
.recent-tag.late { background: rgba(255,64,129,.2); color: var(--cockpit-accent-3); }
</style>
