<script setup lang="ts">
const cards = [
  { title: '在管项目', value: '—' },
  { title: '团队人数', value: '—' },
  { title: '本月毛利 (HKD)', value: '—' },
  { title: '累计节省 (HKD)', value: '—' },
]
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="6" v-for="card in cards" :key="card.title">
      <el-card shadow="hover">
        <div style="color: #909399; font-size: 13px">{{ card.title }}</div>
        <div style="font-size: 28px; font-weight: 600; margin-top: 8px">{{ card.value }}</div>
      </el-card>
    </el-col>
  </el-row>

  <el-card style="margin-top: 16px">
    <template #header>欢迎</template>
    <p>Phase 0 框架已就绪。左侧菜单对应管理后台 8 大维度：</p>
    <ol>
      <li>项目管理（含风险/合规）</li>
      <li>员工派单（含资源利用率）</li>
      <li>利润管理（三层成本透视）</li>
      <li>外部支出管理（耗材/分包/临时人力/许可/差旅）</li>
      <li>项目完成效率</li>
      <li>技术沉淀 / 知识资产 ⭐</li>
      <li>工程师能力建设 ⭐</li>
      <li>需求方关系 / 复盘 ⭐</li>
    </ol>
    <p>Phase 1 起按维度逐项实现具体功能。</p>
  </el-card>
</template>
