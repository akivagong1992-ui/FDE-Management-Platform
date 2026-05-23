<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getByNeedParty, type ByNeedPartyRow } from '@/api/profit'

const rows = ref<ByNeedPartyRow[]>([])
const loading = ref(false)
const expanded = ref<string[]>([])

async function load() {
  loading.value = true
  try { rows.value = await getByNeedParty() } finally { loading.value = false }
}

function fmt(n: number): string {
  return new Intl.NumberFormat('en-HK', { minimumFractionDigits: 2 }).format(n)
}

function rowKey(r: ByNeedPartyRow): string { return String(r.need_party_id) }

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-alert type="info" :closable="false" style="margin-bottom: 12px">
      <strong>口径 B · 按客户 / 需求方汇总</strong>：判断哪个客户欠款、是否亏损、是否值得继续合作。
    </el-alert>

    <el-table
      :data="rows" :row-key="rowKey" :expand-row-keys="expanded"
      @expand-change="(_r, exp) => expanded = (exp as ByNeedPartyRow[]).map(r => String(r.need_party_id))"
      stripe
    >
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding: 0 32px">
            <el-table :data="row.projects" size="small">
              <el-table-column prop="project_code" label="编号" width="100" />
              <el-table-column prop="project_name" label="项目" min-width="200" />
              <el-table-column prop="sales_person_name" label="销售" width="120" />
              <el-table-column prop="status" label="状态" width="100" />
              <el-table-column label="收入" width="140" align="right">
                <template #default="{ row: p }">HK$ {{ fmt(p.revenue) }}</template>
              </el-table-column>
              <el-table-column label="成本" width="140" align="right">
                <template #default="{ row: p }">HK$ {{ fmt(p.cost) }}</template>
              </el-table-column>
              <el-table-column label="毛利" width="140" align="right">
                <template #default="{ row: p }">
                  <span :style="{ color: p.margin >= 0 ? '#67c23a' : '#f56c6c', fontWeight: 600 }">
                    HK$ {{ fmt(p.margin) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="need_party_name" label="客户 / 需求方" min-width="180" />
      <el-table-column prop="project_count" label="项目数" width="100" />
      <el-table-column label="累计收入" width="160" align="right">
        <template #default="{ row }">HK$ {{ fmt(row.revenue) }}</template>
      </el-table-column>
      <el-table-column label="累计成本" width="160" align="right">
        <template #default="{ row }">HK$ {{ fmt(row.cost) }}</template>
      </el-table-column>
      <el-table-column label="累计毛利" width="160" align="right">
        <template #default="{ row }">
          <el-tag :type="row.margin >= 0 ? 'success' : 'danger'" effect="dark">
            HK$ {{ fmt(row.margin) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
