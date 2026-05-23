<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import CountNumber from '@/components/CountNumber.vue'
import {
  getOverview, getProjectBoard, getSavingsAndValue,
  type OverviewKpi, type ProjectBoard, type SavingsAndValue,
} from '@/api/cockpit'

const overview = ref<OverviewKpi | null>(null)
const sav = ref<SavingsAndValue | null>(null)
const board = ref<ProjectBoard | null>(null)
let refreshTimer: number | undefined

async function load() {
  try {
    const [o, s, b] = await Promise.all([getOverview(), getSavingsAndValue(), getProjectBoard()])
    overview.value = o
    sav.value = s
    board.value = b
  } catch {
    /* keep last successful snapshot on transient errors */
  }
}

const cTotal = computed(() => (sav.value?.total_c_view ?? 0) / 10000)
const activeProjects = computed(() => overview.value?.active_projects ?? 0)
const teamSize = computed(() => overview.value?.team_size ?? 0)
const completedThisMonth = computed(() => overview.value?.completed_this_month ?? 0)
const showcaseClients = computed(() => overview.value?.showcase_clients ?? [])
const capabilities = computed(() => overview.value?.capability_by_category ?? [])
const maxCap = computed(() => Math.max(1, ...capabilities.value.map((c) => c.engineer_count)))

// ── HK map (来自原 Tab 2，简化为只读展示，无 click-to-filter) ─────
const DISTRICT_LABELS: Record<string, string> = {
  HK_ISLAND: '港岛', KOWLOON: '九龙', NT_EAST: '新界东',
  NT_WEST: '新界西', OUTLYING: '离岛',
}
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
  for (const d of board.value?.by_district || []) m[d.code] = d.count
  return m
})

const mapEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
const mapError = ref<string | null>(null)

function withAlpha(hex: string, a: number): string {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}

async function loadMap() {
  if (!mapEl.value) return
  try {
    const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/810000_full.json')
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const geo = await resp.json()
    echarts.registerMap('HK', geo)
    chart = echarts.init(mapEl.value)
    renderMap()
  } catch (e: unknown) {
    mapError.value = e instanceof Error ? e.message : 'fetch failed'
  }
}

function renderMap() {
  if (!chart) return
  const counts = districtCount.value
  const seriesData = Object.entries(DISTRICT_TO_MACRO).map(([dist, macro]) => ({
    name: dist,
    value: counts[macro] || 0,
    macro,
    itemStyle: {
      areaColor: counts[macro]
        ? withAlpha(MACRO_COLOR[macro], 0.55)
        : 'rgba(0,229,255,.06)',
      borderColor: 'rgba(0,229,255,.6)', borderWidth: 1,
    },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0a1929',
      borderColor: 'var(--cockpit-accent)',
      textStyle: { color: '#cfe3ff' },
      formatter: (p: { name: string; value: number; data?: { macro?: string } }) => {
        const macro = p.data?.macro
        const label = macro ? DISTRICT_LABELS[macro] || macro : ''
        return `<b>${p.name}</b> (${label})<br/>项目数: ${p.value}`
      },
    },
    geo: {
      map: 'HK', roam: false, zoom: 1.15,
      label: { show: true, color: '#cfe3ff', fontSize: 10 },
      itemStyle: { areaColor: 'rgba(0,30,60,.3)', borderColor: 'rgba(0,229,255,.4)' },
      emphasis: { label: { color: '#fff', fontSize: 12 }, itemStyle: { areaColor: 'rgba(255,64,129,.4)' } },
    },
    series: [
      {
        name: 'HK', type: 'map', map: 'HK', roam: false, zoom: 1.15,
        data: seriesData,
        label: { show: true, color: '#cfe3ff', fontSize: 10 },
        emphasis: {
          label: { color: '#fff', fontSize: 12 },
          itemStyle: { areaColor: 'rgba(255,64,129,.5)' },
        },
      },
    ],
  })
}

function resizeChart() { chart?.resize() }

onMounted(async () => {
  await load()
  await nextTick()
  await loadMap()
  refreshTimer = window.setInterval(async () => {
    await load()
    renderMap()
  }, 60000)
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (chart) chart.dispose()
  window.removeEventListener('resize', resizeChart)
})
</script>

<template>
  <div class="grid">
    <!-- KPI 4 卡 -->
    <div class="kpi-row">
      <div class="panel kpi-card">
        <div class="kpi-label">在管项目</div>
        <div class="kpi-value glow-text"><CountNumber :value="activeProjects" /></div>
      </div>
      <div class="panel kpi-card brag">
        <div class="kpi-label">降本金额</div>
        <div class="kpi-value glow-text">
          <CountNumber :value="cTotal" :decimals="1" /><span class="unit">万 HKD</span>
        </div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">团队规模</div>
        <div class="kpi-value glow-text"><CountNumber :value="teamSize" /></div>
      </div>
      <div class="panel kpi-card">
        <div class="kpi-label">本月完成</div>
        <div class="kpi-value glow-text">
          <CountNumber :value="completedThisMonth" /><span class="unit">个</span>
        </div>
      </div>
    </div>

    <!-- 下方主区：左侧上下两卡（能力矩阵 / 已交付客户）+ 右侧地图 -->
    <div class="lower">
      <div class="left-col">
        <div class="panel">
          <div class="panel-title">能力矩阵</div>
          <div v-if="capabilities.length === 0" class="empty">暂无技能登记</div>
          <div v-else class="cap-grid">
            <div v-for="c in capabilities" :key="c.category" class="cap-cell">
              <div class="cap-name">{{ c.category }}</div>
              <div class="cap-bar">
                <div class="cap-fill" :style="{ width: `${(c.engineer_count / maxCap) * 100}%` }" />
              </div>
              <div class="cap-num">
                <CountNumber :value="c.engineer_count" /> 人
              </div>
            </div>
          </div>
          <div class="cap-meta" v-if="capabilities.length > 0">
            覆盖 <strong class="hi">{{ capabilities.length }}</strong> 个技能领域
            / 团队总规模 <strong class="hi">{{ teamSize }}</strong> 人
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">合作客户（{{ showcaseClients.length }}）</div>
          <div v-if="showcaseClients.length === 0" class="empty">
            管理后台「客户列表」勾选「驾驶舱展示」+ 上传 Logo 即出现
          </div>
          <div v-else class="logo-grid">
            <div v-for="(c, i) in showcaseClients" :key="i" class="logo-tile" :title="c.name">
              <img :src="`/api/uploads/${c.logo_path}`" :alt="c.name" class="logo-img" />
              <div class="logo-name">{{ c.name }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel map-panel">
        <div class="panel-title">
          香港项目分布
          <span v-if="mapError" class="map-err" :title="mapError">⚠ 地图数据加载失败</span>
        </div>
        <div v-show="!mapError" ref="mapEl" class="echarts-map"></div>
        <div v-if="mapError" class="empty">地图数据需联网拉取 (DataV CDN)</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: flex; flex-direction: column; height: 100%; gap: 16px;
}
.kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; height: 140px;
}
.kpi-card {
  display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;
}
.kpi-card.brag {
  border-color: var(--cockpit-accent-3);
  box-shadow: 0 0 24px rgba(255, 64, 129, 0.35);
}
.kpi-card.brag .kpi-value {
  color: var(--cockpit-accent-3);
  text-shadow: 0 0 8px var(--cockpit-accent-3), 0 0 16px rgba(255, 64, 129, 0.5);
}
.unit { font-size: 0.4em; margin-left: 8px; color: var(--cockpit-text-dim); font-weight: normal; }

.map-panel { display: flex; flex-direction: column; }
.echarts-map { flex: 1; min-height: 320px; }
.map-err { margin-left: 12px; color: #ff8e00; font-size: 11px; }

.lower {
  flex: 1; display: grid; grid-template-columns: 1fr 1.1fr; gap: 16px; min-height: 0;
}
.left-col {
  display: grid; grid-template-rows: 1fr 1fr; gap: 16px; min-height: 0;
}
.empty {
  display: flex; align-items: center; justify-content: center;
  height: calc(100% - 30px); color: var(--cockpit-text-dim);
}

/* 能力矩阵 */
.cap-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.cap-cell {
  display: grid; grid-template-columns: 90px 1fr 70px; gap: 12px; align-items: center;
}
.cap-name { color: var(--cockpit-text); font-size: 14px; }
.cap-bar {
  height: 14px; background: rgba(0, 229, 255, 0.08);
  border: 1px solid var(--cockpit-border); border-radius: 999px; overflow: hidden;
}
.cap-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cockpit-accent), var(--cockpit-accent-2));
  box-shadow: 0 0 8px var(--cockpit-accent);
  transition: width 0.6s ease;
}
.cap-num {
  font-family: 'Courier New', monospace;
  color: var(--cockpit-accent); font-weight: 600;
  text-align: right;
}
.cap-meta {
  margin-top: 16px;
  color: var(--cockpit-text-dim);
  font-size: 12px;
  letter-spacing: 1px;
}
.hi { color: var(--cockpit-accent); font-family: 'Courier New', monospace; padding: 0 2px; }

/* 已交付客户 logo 矩阵 */
.logo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px; margin-top: 12px;
  align-content: flex-start;
}
.logo-tile {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--cockpit-border);
  border-radius: 10px;
  transition: all 0.3s;
  min-height: 92px;
}
.logo-tile:hover {
  background: rgba(0, 229, 255, 0.10);
  border-color: var(--cockpit-accent);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
}
.logo-img {
  max-width: 80px; max-height: 44px;
  object-fit: contain;
  filter: brightness(1.1);
}
.logo-name {
  margin-top: 8px;
  font-size: 11px;
  color: var(--cockpit-text-dim);
  text-align: center;
  letter-spacing: 0.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
</style>
