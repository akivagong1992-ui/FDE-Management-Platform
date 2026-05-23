<script setup lang="ts">
import TabPlaceholder from '@/components/TabPlaceholder.vue'
</script>
<template>
  <TabPlaceholder
    :tab-no="4"
    title="工程师视图"
    plan-section="PLAN §4.10 Tab 4"
    :indicators="[
      '团队规模增长曲线',
      '技能矩阵雷达图',
      'Top 5 满负荷工程师',
      'Vendor 分布饼图',
    ]"
  />
</template>
