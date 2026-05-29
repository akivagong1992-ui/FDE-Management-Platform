<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getBySalesPerson, type BySalesRow } from '@/api/profit'
import { fmt2 as fmt } from '@/utils/format'

const rows = ref<BySalesRow[]>([])
const loading = ref(false)
const expanded = ref<string[]>([])

async function load() {
  loading.value = true
  try { rows.value = await getBySalesPerson() } finally { loading.value = false }
}

function rowKey(r: BySalesRow): string { return String(r.sales_person_id) }

const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收',
  archived: '归档',
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-table
      :data="rows" :row-key="rowKey" :expand-row-keys="expanded"
      @expand-change="(_r, exp) => expanded = (exp as BySalesRow[]).map(r => String(r.sales_person_id))"
      stripe
    >
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding: 0 32px">
            <el-table :data="row.projects" size="small">
              <el-table-column prop="project_code" label="编号" width="100" />
              <el-table-column label="项目" min-width="200">
                <template #default="{ row: p }">
                  <el-tag v-if="p.kind === 'no_revenue'" type="warning" size="small" style="margin-right: 6px">无收入</el-tag>
                  {{ p.project_name }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row: p }">{{ STATUS_LABEL[p.status] || p.status }}</template>
              </el-table-column>
              <el-table-column label="收入 (HKD)" width="150" align="right">
                <template #default="{ row: p }">{{ fmt(p.revenue) }}</template>
              </el-table-column>
              <el-table-column label="成本 (HKD)" width="150" align="right">
                <template #default="{ row: p }">{{ fmt(p.cost) }}</template>
              </el-table-column>
              <el-table-column label="毛利 (HKD)" width="150" align="right">
                <template #default="{ row: p }">
                  <span :style="{ color: p.margin >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 600 }">
                    {{ fmt(p.margin) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="sales_person_name" label="销售人员" min-width="140" />
      <el-table-column prop="project_count" label="项目数" width="100" />
      <el-table-column label="累计收入 (HKD)" width="170" align="right">
        <template #default="{ row }">{{ fmt(row.revenue) }}</template>
      </el-table-column>
      <el-table-column label="累计成本 (HKD)" width="170" align="right">
        <template #default="{ row }">{{ fmt(row.cost) }}</template>
      </el-table-column>
      <el-table-column label="累计毛利 (HKD)" width="170" align="right">
        <template #default="{ row }">
          <el-tag :type="row.margin >= 0 ? 'success' : 'danger'" effect="dark">
            {{ fmt(row.margin) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
