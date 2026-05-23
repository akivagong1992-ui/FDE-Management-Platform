<script setup lang="ts">
import TabPlaceholder from '@/components/TabPlaceholder.vue'
</script>
<template>
  <TabPlaceholder
    :tab-no="2"
    title="项目地图"
    plan-section="PLAN §4.10 Tab 2"
    :indicators="[
      '香港地图标点（每点 = 一个在管项目）',
      '点击 / 自动轮播显示项目卡片',
      '按地区 / 状态分色',
    ]"
  />
</template>
