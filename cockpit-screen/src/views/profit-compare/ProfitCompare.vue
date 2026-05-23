<script setup lang="ts">
import TabPlaceholder from '@/components/TabPlaceholder.vue'
</script>
<template>
  <TabPlaceholder
    :tab-no="3"
    title="利润对比（最 brag 的一屏）"
    plan-section="PLAN §4.10 Tab 3"
    :indicators="[
      '本季度 vs 上季度毛利',
      '内化模式 vs 传统外包模式估算 — 累计节省金额',
      'Vendor 性价比榜（服务费 / 真实成本 比）',
      '毛利率趋势',
    ]"
  />
</template>
