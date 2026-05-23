<script setup lang="ts">
import TabPlaceholder from '@/components/TabPlaceholder.vue'
</script>
<template>
  <TabPlaceholder
    :tab-no="8"
    title="客户口碑 ⭐"
    plan-section="PLAN §4.10 Tab 8"
    :indicators="[
      '验收平均满意度雷达',
      '续单率仪表盘',
      '复盘行动项闭环率',
      '需求方关系热度图',
    ]"
  />
</template>
