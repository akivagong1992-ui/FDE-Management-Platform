<script setup lang="ts">
import { ref } from 'vue'
import EngineerList from './EngineerList.vue'
import VendorList from './VendorList.vue'
import SkillCatalog from './SkillCatalog.vue'

const tab = ref<'engineers' | 'vendors' | 'skills'>('engineers')
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">② 员工派单 · 人员档案</span>
        <el-tag type="info">Phase 1a — 工程师 + Vendor + 技能字典已落地（派单/工时见 Phase 1c）</el-tag>
      </div>
    </template>
    <el-tabs v-model="tab">
      <el-tab-pane label="工程师档案" name="engineers"><EngineerList v-if="tab === 'engineers'" /></el-tab-pane>
      <el-tab-pane label="Vendor 档案" name="vendors"><VendorList v-if="tab === 'vendors'" /></el-tab-pane>
      <el-tab-pane label="技能字典" name="skills"><SkillCatalog v-if="tab === 'skills'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
