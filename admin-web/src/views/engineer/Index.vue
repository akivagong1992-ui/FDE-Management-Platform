<script setup lang="ts">
import { ref } from 'vue'
import AssignmentList from './AssignmentList.vue'
import TimesheetEntry from './TimesheetEntry.vue'
import EngineerList from './EngineerList.vue'
import VendorList from './VendorList.vue'
import SkillCatalog from './SkillCatalog.vue'

type Tab = 'assignments' | 'timesheets' | 'engineers' | 'vendors' | 'skills'
const tab = ref<Tab>('assignments')
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">② 员工派单</span>
        <el-tag type="success">Phase 1c — 派单 + 工时（含 Excel 导入）已落地</el-tag>
      </div>
    </template>
    <el-tabs v-model="tab">
      <el-tab-pane label="派单管理" name="assignments"><AssignmentList v-if="tab === 'assignments'" /></el-tab-pane>
      <el-tab-pane label="工时记录" name="timesheets"><TimesheetEntry v-if="tab === 'timesheets'" /></el-tab-pane>
      <el-tab-pane label="工程师档案" name="engineers"><EngineerList v-if="tab === 'engineers'" /></el-tab-pane>
      <el-tab-pane label="Vendor 档案" name="vendors"><VendorList v-if="tab === 'vendors'" /></el-tab-pane>
      <el-tab-pane label="技能字典" name="skills"><SkillCatalog v-if="tab === 'skills'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
