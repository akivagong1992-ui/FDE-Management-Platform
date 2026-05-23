<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { getProjectBoard, type ProjectBoard, type ProjectBoardItem } from '@/api/cockpit'

const data = ref<ProjectBoard | null>(null)
let timer: number | undefined

async function load() { try { data.value = await getProjectBoard() } catch { /* keep */ } }

const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收',
  closing: '收尾', archived: '归档',
}
const STATUS_COLOR: Record<string, string> = {
  drafting: '#7c4dff', in_progress: '#00e5ff', accepting: '#ffe082',
  closing: '#ff80ab', archived: '#6b7d97',
}

function projColor(p: ProjectBoardItem): string {
  return STATUS_COLOR[p.status] || '#6b7d97'
}

onMounted(async () => { await load(); timer = window.setInterval(load, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="grid">
    <div class="status-row">
      <div v-for="s in data?.by_status || []" :key="s.label" class="panel status-pill">
        <div class="status-label">{{ STATUS_LABEL[s.label] || s.label }}</div>
        <div class="status-count" :style="{ color: STATUS_COLOR[s.label] || '#cfe3ff' }">{{ s.count }}</div>
      </div>
      <div class="panel status-pill total">
        <div class="status-label">在管项目合计</div>
        <div class="status-count glow-text">{{ data?.total ?? '—' }}</div>
      </div>
    </div>

    <div class="panel cards-area">
      <div class="panel-title">项目看板（最新 {{ data?.items.length ?? 0 }} 个）</div>
      <div class="grid-cards">
        <div v-for="p in data?.items || []" :key="p.project_id" class="card"
             :style="{ borderLeftColor: projColor(p) }">
          <div class="card-name">{{ p.name }}</div>
          <div class="card-meta">
            <span class="badge" :style="{ background: projColor(p) }">{{ STATUS_LABEL[p.status] || p.status }}</span>
            <span class="badge" :class="p.kind === 'revenue' ? 'badge-rev' : 'badge-norev'">
              {{ p.kind === 'revenue' ? '有收入' : '无收入' }}
            </span>
          </div>
          <div class="card-row"><span class="k">客户</span>{{ p.need_party || '—' }}</div>
          <div class="card-row"><span class="k">销售</span>{{ p.sales_person || '—' }}</div>
          <div class="card-row"><span class="k">期间</span>
            {{ p.planned_start || '—' }} → {{ p.planned_end || '—' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.status-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; height: 90px; }
.status-pill {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.status-pill.total { border-color: var(--cockpit-accent); }
.status-label { color: var(--cockpit-text-dim); font-size: 12px; letter-spacing: 2px; }
.status-count {
  font-family: 'Courier New', monospace; font-size: 28px; font-weight: 700; margin-top: 4px;
}

.cards-area { flex: 1; overflow: hidden; }
.grid-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  margin-top: 12px; max-height: calc(100% - 40px); overflow-y: auto;
}
.card {
  background: rgba(10, 25, 41, 0.6); border: 1px solid var(--cockpit-border);
  border-left: 4px solid var(--cockpit-accent);
  padding: 12px; border-radius: 2px;
}
.card-name { color: var(--cockpit-text); font-weight: 600; font-size: 14px; margin-bottom: 8px; }
.card-meta { display: flex; gap: 6px; margin-bottom: 8px; }
.badge { font-size: 11px; padding: 2px 6px; border-radius: 2px; color: #061327; font-weight: 600; }
.badge-rev { background: #00e5ff; }
.badge-norev { background: #ffe082; }
.card-row { font-size: 12px; color: var(--cockpit-text-dim); margin: 4px 0; }
.k { display: inline-block; width: 40px; color: var(--cockpit-text-dim); }
</style>
