<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getEngineerStats, type EngineerStats } from '@/api/cockpit'

const data = ref<EngineerStats | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getEngineerStats() } catch { /* keep */ } }

const maxVendor = computed(() => Math.max(1, ...(data.value?.by_vendor || []).map((v) => v.count)))
const maxAlloc = computed(() => Math.max(1, ...(data.value?.top_allocated || []).map((e) => e.alloc_pct)))

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div class="panel kpi-card brag">
        <div class="kpi-label">团队规模</div>
        <div class="kpi-value glow-text">{{ data?.total ?? '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">在场工程师</div>
        <div class="kpi-value glow-text">{{ data?.active ?? '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">合作 Vendor 数</div>
        <div class="kpi-value glow-text">{{ data?.by_vendor.length ?? '—' }}</div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">技能等级分布</div>
        <div class="level-strip">
          <div v-for="l in data?.by_level || []" :key="l.level" class="level-cell">
            <span class="level-tag">L{{ l.level }}</span>
            <span class="level-num">{{ l.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel">
        <div class="panel-title">Vendor 分布</div>
        <div v-if="!data?.by_vendor.length" class="empty">暂无数据</div>
        <div v-else class="bar-list">
          <div v-for="v in data.by_vendor" :key="v.vendor_id" class="bar-row">
            <div class="bar-label">{{ v.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${(v.count / maxVendor) * 100}%` }" />
            </div>
            <div class="bar-num">{{ v.count }} 人</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">Top 满负荷工程师（按当前派单 % 加总）</div>
        <div v-if="!data?.top_allocated.length" class="empty">暂无派单</div>
        <div v-else class="bar-list">
          <div v-for="e in data.top_allocated" :key="e.engineer_id" class="bar-row">
            <div class="bar-label">{{ e.name }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${Math.min((e.alloc_pct / maxAlloc) * 100, 100)}%` }" />
            </div>
            <div class="bar-num">{{ e.alloc_pct }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px; }
.kpi-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 12px; }
.kpi-card.brag { border-color: var(--cockpit-accent-3); box-shadow: 0 0 24px rgba(255,64,129,.35); }
.kpi-card.brag .kpi-value { color: var(--cockpit-accent-3); text-shadow: 0 0 8px var(--cockpit-accent-3); }
.level-strip { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; justify-content: center; }
.level-cell {
  display: flex; flex-direction: column; align-items: center;
  padding: 4px 8px; border: 1px solid var(--cockpit-border); border-radius: 2px;
}
.level-tag { color: var(--cockpit-accent); font-size: 11px; font-weight: 600; }
.level-num { color: var(--cockpit-text); font-family: 'Courier New', monospace; font-weight: 700; }

.lower { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; min-height: 0; }
.empty {
  display: flex; align-items: center; justify-content: center;
  height: calc(100% - 30px); color: var(--cockpit-text-dim); font-size: 13px;
}
.bar-list { display: flex; flex-direction: column; gap: 14px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 140px 1fr 80px; gap: 12px; align-items: center; }
.bar-label { color: var(--cockpit-text); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { height: 14px; background: rgba(0,229,255,.08); border: 1px solid var(--cockpit-border); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2)); box-shadow: 0 0 8px var(--cockpit-accent); }
.bar-num { font-family: 'Courier New', monospace; color: var(--cockpit-accent); font-weight: 600; text-align: right; font-size: 13px; }
</style>
