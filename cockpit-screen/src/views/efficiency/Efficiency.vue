<script setup lang="ts">
import TabPlaceholder from '@/components/TabPlaceholder.vue'
</script>
<template>
  <TabPlaceholder
    :tab-no="5"
    title="效率榜"
    plan-section="PLAN §4.10 Tab 5"
    :indicators="[
      '当月 Top 项目（按毛利）',
      'Top 工程师（按人均产出）',
      '按时交付率仪表盘',
      '返工 / 变更次数',
    ]"
  />
</template>
