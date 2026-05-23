<script setup lang="ts">
defineProps<{
  title: string
  tabNo: number
  planSection: string
  indicators: string[]
}>()
</script>

<template>
  <div class="placeholder-grid">
    <div class="panel head">
      <div class="panel-title">Tab {{ String(tabNo).padStart(2, '0') }} · {{ title }}</div>
      <div class="hint">
        本页 Phase 0 仅作壳子展示，对接真实数据见 {{ planSection }}。
      </div>
    </div>
    <div class="panel indicators">
      <div class="panel-title">候选指标</div>
      <ul>
        <li v-for="(it, i) in indicators" :key="i">{{ it }}</li>
      </ul>
    </div>
    <div class="panel large">
      <div class="panel-title">主图表区</div>
      <div class="big-placeholder">
        <div class="big-icon">📊</div>
        <div class="big-text">Phase 3 接入真实数据</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.placeholder-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr;
  gap: 16px;
  height: 100%;
}
.head { grid-column: 1 / -1; }
.large { grid-column: 1 / -1; }
.hint { color: var(--cockpit-text-dim); font-size: 14px; }
.indicators ul { margin: 0; padding-left: 20px; color: var(--cockpit-text); line-height: 2; }
.big-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100% - 30px);
  border: 1px dashed var(--cockpit-border);
  border-radius: 10px;
  gap: 8px;
}
.big-icon { font-size: 64px; opacity: 0.5; }
.big-text { color: var(--cockpit-text-dim); letter-spacing: 2px; }
</style>
