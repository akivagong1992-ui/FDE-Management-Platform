<script setup lang="ts">
import { ref } from 'vue'
import AssignmentList from './AssignmentList.vue'
import TimesheetEntry from './TimesheetEntry.vue'
import EngineerList from './EngineerList.vue'
import SkillCatalog from './SkillCatalog.vue'

type Tab = 'assignments' | 'timesheets' | 'engineers' | 'skills'
const tab = ref<Tab>('assignments')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="派单管理" name="assignments"><AssignmentList v-if="tab === 'assignments'" /></el-tab-pane>
      <el-tab-pane label="工时管理" name="timesheets"><TimesheetEntry v-if="tab === 'timesheets'" /></el-tab-pane>
      <el-tab-pane label="工程师管理" name="engineers"><EngineerList v-if="tab === 'engineers'" /></el-tab-pane>
      <el-tab-pane label="能力矩阵管理" name="skills"><SkillCatalog v-if="tab === 'skills'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
