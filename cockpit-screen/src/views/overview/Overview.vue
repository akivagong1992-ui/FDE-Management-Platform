<script setup lang="ts">
import { ref } from 'vue'

interface Kpi { label: string; value: string; unit?: string }

const kpis = ref<Kpi[]>([
  { label: '在管项目', value: '14' },
  { label: '累计毛利', value: '1,284', unit: '万 HKD' },
  { label: '团队规模', value: '87' },
  { label: '累计节省', value: '356', unit: '万 HKD' },
])
</script>

<template>
  <div class="grid">
    <div class="kpi-row">
      <div v-for="k in kpis" :key="k.label" class="panel kpi-card">
        <div class="kpi-label">{{ k.label }}</div>
        <div class="kpi-value glow-text">
          {{ k.value }}<span class="unit">{{ k.unit || '' }}</span>
        </div>
      </div>
    </div>

    <div class="lower">
      <div class="panel area-map">
        <div class="panel-title">香港项目分布</div>
        <div class="placeholder">[ 香港地图 · ECharts geoJSON 占位 — Phase 3 接入 ]</div>
      </div>
      <div class="panel area-trend">
        <div class="panel-title">月度毛利曲线</div>
        <div class="placeholder">[ ECharts 折线图占位 — Phase 3 接入 ]</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  height: 140px;
}
.kpi-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}
.unit {
  font-size: 0.4em;
  margin-left: 8px;
  color: var(--cockpit-text-dim);
  font-weight: normal;
}
.lower {
  flex: 1;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  min-height: 0;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100% - 30px);
  color: var(--cockpit-text-dim);
  letter-spacing: 2px;
  font-size: 14px;
  border: 1px dashed var(--cockpit-border);
  border-radius: 2px;
}
</style>
