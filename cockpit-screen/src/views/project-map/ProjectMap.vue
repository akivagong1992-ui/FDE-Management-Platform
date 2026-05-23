<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
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

// HK 18 districts → our 5 macro regions
const DISTRICT_TO_MACRO: Record<string, string> = {
  '中西区': 'HK_ISLAND', '湾仔区': 'HK_ISLAND', '东区': 'HK_ISLAND', '南区': 'HK_ISLAND',
  '油尖旺区': 'KOWLOON', '深水埗区': 'KOWLOON', '九龙城区': 'KOWLOON',
  '黄大仙区': 'KOWLOON', '观塘区': 'KOWLOON',
  '沙田区': 'NT_EAST', '大埔区': 'NT_EAST', '北区': 'NT_EAST', '西贡区': 'NT_EAST',
  '葵青区': 'NT_WEST', '荃湾区': 'NT_WEST', '屯门区': 'NT_WEST', '元朗区': 'NT_WEST',
  '离岛区': 'OUTLYING',
}

const MACRO_COLOR: Record<string, string> = {
  HK_ISLAND: '#00e5ff', KOWLOON: '#7c4dff', NT_EAST: '#67ff8a',
  NT_WEST: '#ffe082', OUTLYING: '#ff80ab',
}

const districtCount = computed(() => {
  const m: Record<string, number> = {}
  for (const d of data.value?.by_district || []) m[d.code] = d.count
  return m
})

const selectedDistrict = ref<string | null>(null)
const selectedItems = computed(() => {
  if (!selectedDistrict.value) return data.value?.items?.slice(0, 6) || []
  return (data.value?.items || []).filter((it) => it.district === selectedDistrict.value).slice(0, 8)
})

function projColor(p: ProjectBoardItem): string {
  return STATUS_COLOR[p.status] || '#6b7d97'
}

// ─── ECharts map ───
const mapEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const mapLoaded = ref(false)
const mapError = ref<string | null>(null)

async function loadMap() {
  if (!mapEl.value) return
  try {
    const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/810000_full.json')
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const geo = await resp.json()
    echarts.registerMap('HK', geo)
    chart = echarts.init(mapEl.value)
    renderMap()
    mapLoaded.value = true
  } catch (e: any) {
    mapError.value = e?.message || 'fetch failed'
  }
}

function renderMap() {
  if (!chart || !mapLoaded.value) return
  const counts = districtCount.value
  const seriesData = Object.entries(DISTRICT_TO_MACRO).map(([dist, macro]) => ({
    name: dist,
    value: counts[macro] || 0,
    macro,
    itemStyle: {
      areaColor: counts[macro]
        ? withAlpha(MACRO_COLOR[macro], 0.55)
        : 'rgba(0,229,255,.06)',
      borderColor: selectedDistrict.value === macro ? '#ff4081' : 'rgba(0,229,255,.6)',
      borderWidth: selectedDistrict.value === macro ? 2.5 : 1,
    },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0a1929',
      borderColor: 'var(--cockpit-accent)',
      textStyle: { color: '#cfe3ff' },
      formatter: (p: any) => {
        const macro = p.data?.macro
        const label = DISTRICT_LABELS[macro] || macro
        return `<b>${p.name}</b> (${label})<br/>项目数: ${p.value}`
      },
    },
    geo: {
      map: 'HK',
      roam: false,
      zoom: 1.15,
      label: {
        show: true, color: '#cfe3ff', fontSize: 10,
      },
      itemStyle: {
        areaColor: 'rgba(0,30,60,.3)',
        borderColor: 'rgba(0,229,255,.4)',
      },
      emphasis: {
        label: { color: '#fff', fontSize: 12 },
        itemStyle: { areaColor: 'rgba(255,64,129,.4)' },
      },
    },
    series: [
      {
        name: 'HK',
        type: 'map',
        map: 'HK',
        roam: false,
        zoom: 1.15,
        data: seriesData,
        label: { show: true, color: '#cfe3ff', fontSize: 10 },
        emphasis: {
          label: { color: '#fff', fontSize: 12 },
          itemStyle: { areaColor: 'rgba(255,64,129,.5)' },
        },
      },
    ],
  })

  chart.off('click')
  chart.on('click', (p: any) => {
    const macro = (p.data as any)?.macro
    if (!macro) return
    selectedDistrict.value = selectedDistrict.value === macro ? null : macro
    renderMap()
  })
}

watch([districtCount, selectedDistrict], () => renderMap())

onMounted(async () => {
  await load()
  await nextTick()
  await loadMap()
  timer = window.setInterval(async () => {
    await load()
    renderMap()
  }, 60000)
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (chart) chart.dispose()
  window.removeEventListener('resize', resizeChart)
})

function resizeChart() { chart?.resize() }

function withAlpha(hex: string, a: number): string {
  // simple hex → rgba
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}
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
          香港项目分布
          <span v-if="selectedDistrict" class="reset" @click="selectedDistrict = null; renderMap()">[清除选区]</span>
          <span v-if="mapError" class="map-err" :title="mapError">⚠ 地图数据加载失败，显示备用 schematic</span>
        </div>

        <!-- Real HK map (ECharts) -->
        <div v-show="!mapError" ref="mapEl" class="echarts-map"></div>

        <!-- Fallback SVG schematic -->
        <svg v-if="mapError" viewBox="0 0 800 400" style="width: 100%; height: calc(100% - 30px)">
          <rect width="800" height="400" fill="rgba(0,30,60,.3)" />
          <g v-for="(label, code) in DISTRICT_LABELS" :key="code"
             style="cursor: pointer"
             @click="selectedDistrict = (selectedDistrict === code ? null : code)">
            <rect :x="50 + (Object.keys(DISTRICT_LABELS).indexOf(code) % 3) * 250"
                  :y="40 + Math.floor(Object.keys(DISTRICT_LABELS).indexOf(code) / 3) * 160"
                  width="230" height="140"
                  :fill="districtCount[code] ? `rgba(0,229,255,${0.15 + (districtCount[code] / 8) * 0.5})` : 'rgba(0,229,255,.05)'"
                  :stroke="selectedDistrict === code ? '#ff4081' : 'rgba(0,229,255,.5)'"
                  stroke-width="1.5" rx="4" />
            <text :x="50 + (Object.keys(DISTRICT_LABELS).indexOf(code) % 3) * 250 + 115"
                  :y="40 + Math.floor(Object.keys(DISTRICT_LABELS).indexOf(code) / 3) * 160 + 60"
                  text-anchor="middle" font-size="20" fill="#cfe3ff" font-weight="600">{{ label }}</text>
            <text :x="50 + (Object.keys(DISTRICT_LABELS).indexOf(code) % 3) * 250 + 115"
                  :y="40 + Math.floor(Object.keys(DISTRICT_LABELS).indexOf(code) / 3) * 160 + 95"
                  text-anchor="middle" font-size="28" fill="#00e5ff"
                  font-family="Courier New" font-weight="700">{{ districtCount[code] || 0 }}</text>
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
.echarts-map { flex: 1; min-height: 300px; }
.reset {
  margin-left: 12px; cursor: pointer; color: var(--cockpit-accent-3);
  font-size: 12px; letter-spacing: 1px;
}
.map-err {
  margin-left: 12px; color: #ff8e00; font-size: 11px;
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
