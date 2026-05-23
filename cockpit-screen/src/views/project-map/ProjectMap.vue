<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
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

const DISTRICT_LABELS: Record<string, string> = {
  HK_ISLAND: '港岛', KOWLOON: '九龙', NT_EAST: '新界东',
  NT_WEST: '新界西', OUTLYING: '离岛',
}

// SVG HK schematic regions (manually laid out — schematic not geographic).
// Coordinates within 800×400 viewBox.
const DISTRICT_RECTS: Record<string, { x: number; y: number; w: number; h: number; label: string }> = {
  NT_WEST:   { x:  50, y:  40, w: 230, h: 120, label: '新界西' },
  NT_EAST:   { x: 300, y:  40, w: 230, h: 120, label: '新界东' },
  KOWLOON:   { x: 175, y: 180, w: 280, h:  80, label: '九龙' },
  HK_ISLAND: { x: 150, y: 280, w: 330, h:  80, label: '港岛' },
  OUTLYING:  { x: 560, y: 200, w: 180, h: 140, label: '离岛' },
}

const districtCount = computed(() => {
  const m: Record<string, number> = {}
  for (const d of data.value?.by_district || []) m[d.code] = d.count
  return m
})

const maxCount = computed(() => Math.max(1, ...Object.values(districtCount.value)))

function fillFor(code: string): string {
  const c = districtCount.value[code] || 0
  if (c === 0) return 'rgba(0,229,255,.05)'
  const ratio = Math.min(c / maxCount.value, 1)
  return `rgba(0, 229, 255, ${0.15 + ratio * 0.6})`
}

const selectedDistrict = ref<string | null>(null)
const selectedItems = computed(() => {
  if (!selectedDistrict.value) return data.value?.items?.slice(0, 6) || []
  return (data.value?.items || []).filter((it) => it.district === selectedDistrict.value).slice(0, 8)
})

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
        <div class="status-label">项目合计</div>
        <div class="status-count glow-text">{{ data?.total ?? '—' }}</div>
      </div>
    </div>

    <div class="lower">
      <div class="panel map-panel">
        <div class="panel-title">
          香港项目分布（schematic）
          <span v-if="selectedDistrict" class="reset" @click="selectedDistrict = null">[清除选区]</span>
        </div>
        <svg viewBox="0 0 800 400" style="width: 100%; height: calc(100% - 30px)">
          <!-- water background -->
          <rect width="800" height="400" fill="rgba(0,30,60,.3)" />
          <!-- districts -->
          <g v-for="(r, code) in DISTRICT_RECTS" :key="code"
             style="cursor: pointer"
             @click="selectedDistrict = (selectedDistrict === code ? null : code)">
            <rect :x="r.x" :y="r.y" :width="r.w" :height="r.h"
                  :fill="fillFor(code)"
                  :stroke="selectedDistrict === code ? '#ff4081' : 'rgba(0,229,255,.5)'"
                  :stroke-width="selectedDistrict === code ? '3' : '1.5'"
                  rx="4" />
            <text :x="r.x + r.w / 2" :y="r.y + r.h / 2 - 8"
                  text-anchor="middle" font-size="20"
                  :fill="districtCount[code] ? '#cfe3ff' : '#6b7d97'"
                  font-weight="600">
              {{ r.label }}
            </text>
            <text :x="r.x + r.w / 2" :y="r.y + r.h / 2 + 24"
                  text-anchor="middle" font-size="28"
                  :fill="districtCount[code] ? '#00e5ff' : '#3a4d68'"
                  font-family="Courier New" font-weight="700">
              {{ districtCount[code] || 0 }}
            </text>
          </g>
        </svg>
      </div>

      <div class="panel">
        <div class="panel-title">
          {{ selectedDistrict ? `${DISTRICT_LABELS[selectedDistrict]} 项目（${selectedItems.length}）` : '最近项目（点击地区筛选）' }}
        </div>
        <div class="proj-list">
          <div v-for="p in selectedItems" :key="p.project_id" class="proj-row"
               :style="{ borderLeftColor: projColor(p) }">
            <div class="proj-name">{{ p.name }}</div>
            <div class="proj-meta">
              <span class="proj-badge" :style="{ background: projColor(p) }">{{ STATUS_LABEL[p.status] || p.status }}</span>
              <span class="proj-client">{{ p.need_party || '—' }}</span>
            </div>
          </div>
          <div v-if="selectedItems.length === 0" class="empty">本区暂无项目</div>
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

.lower { flex: 1; display: grid; grid-template-columns: 1.6fr 1fr; gap: 16px; min-height: 0; }
.map-panel { display: flex; flex-direction: column; }
.reset {
  margin-left: 12px; cursor: pointer; color: var(--cockpit-accent-3);
  font-size: 12px; letter-spacing: 1px;
}

.proj-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; overflow-y: auto; max-height: 100%; }
.proj-row {
  background: rgba(10, 25, 41, 0.6); border: 1px solid var(--cockpit-border);
  border-left: 4px solid var(--cockpit-accent); padding: 10px; border-radius: 2px;
}
.proj-name { color: var(--cockpit-text); font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.proj-meta { display: flex; gap: 8px; align-items: center; }
.proj-badge {
  font-size: 11px; padding: 2px 6px; border-radius: 2px; color: #061327; font-weight: 600;
}
.proj-client { color: var(--cockpit-text-dim); font-size: 12px; }
.empty { color: var(--cockpit-text-dim); padding: 20px; text-align: center; }
</style>
