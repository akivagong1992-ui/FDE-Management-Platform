<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { fetchAvailability, type AvailabilityResp, type EngineerAvailability } from '@/api/availability'
import { listVendors, type Vendor } from '@/api/vendors'

const auth = useAuthStore()
const isManager = computed(() => ['admin', 'lead', 'pm', 'finance'].includes(auth.role || ''))
const isEngineer = computed(() => auth.role === 'engineer')

const weeks = ref(4)
const fromDate = ref<string>(new Date().toISOString().slice(0, 10))
const vendorFilter = ref<number | null>(null)
const vendors = ref<Vendor[]>([])
const resp = ref<AvailabilityResp | null>(null)
const loading = ref(false)
const sortMode = ref<'name' | 'most_free' | 'most_busy'>('most_free')

async function load() {
  loading.value = true
  try {
    resp.value = await fetchAvailability({
      weeks: weeks.value,
      from: fromDate.value,
      vendor_id: vendorFilter.value ?? undefined,
    })
    if (isManager.value && vendors.value.length === 0) vendors.value = await listVendors()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const dates = computed<string[]>(() => resp.value?.engineers[0]?.days.map((d) => d.date) ?? [])
const dayCount = computed(() => dates.value.length)
const weekendIdx = computed<Set<number>>(() => {
  const s = new Set<number>()
  dates.value.forEach((d, i) => {
    const dow = new Date(d).getDay()
    if (dow === 0 || dow === 6) s.add(i)
  })
  return s
})

const sortedEngineers = computed<EngineerAvailability[]>(() => {
  const arr = [...(resp.value?.engineers ?? [])]
  if (sortMode.value === 'most_free') arr.sort((a, b) => b.free_day_count - a.free_day_count)
  else if (sortMode.value === 'most_busy') arr.sort((a, b) => b.busy_day_count - a.busy_day_count)
  else arr.sort((a, b) => a.full_name.localeCompare(b.full_name))
  return arr
})

function shiftDays(delta: number) {
  const d = new Date(fromDate.value)
  d.setDate(d.getDate() + delta)
  fromDate.value = d.toISOString().slice(0, 10)
  load()
}

function shortDate(iso: string): string {
  // 'MM-DD'
  return iso.slice(5)
}
function dowLabel(iso: string): string {
  return ['日', '一', '二', '三', '四', '五', '六'][new Date(iso).getDay()]
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <span style="font-weight: 600">{{ isEngineer ? '我的档期' : '工程师档期' }}</span>
        <el-button-group>
          <el-button size="small" @click="shiftDays(-weeks * 7)">← 上 {{ weeks }} 周</el-button>
          <el-button size="small" @click="fromDate = new Date().toISOString().slice(0,10); load()">今天</el-button>
          <el-button size="small" @click="shiftDays(weeks * 7)">下 {{ weeks }} 周 →</el-button>
        </el-button-group>
        <el-date-picker
          v-model="fromDate" type="date" value-format="YYYY-MM-DD"
          placeholder="起始日" size="small" style="width: 150px"
          @change="load" />
        <el-select v-model="weeks" size="small" style="width: 110px" @change="load">
          <el-option :value="2" label="2 周" />
          <el-option :value="4" label="4 周" />
          <el-option :value="8" label="8 周" />
          <el-option :value="12" label="12 周" />
        </el-select>
        <el-select v-if="isManager" v-model="vendorFilter" clearable filterable placeholder="所有 Vendor"
                   size="small" style="width: 180px" @change="load">
          <el-option v-for="v in vendors" :key="v.id" :label="v.name" :value="v.id" />
        </el-select>
        <el-select v-model="sortMode" size="small" style="width: 130px">
          <el-option value="most_free" label="按最空排序" />
          <el-option value="most_busy" label="按最忙排序" />
          <el-option value="name" label="按姓名排序" />
        </el-select>
        <div style="flex: 1" />
        <span style="color: #909399; font-size: 12px">
          <span style="display: inline-block; width: 12px; height: 12px; background: #f56c6c; vertical-align: middle; margin-right: 4px"></span>忙
          <span style="display: inline-block; width: 12px; height: 12px; background: #e1f3d8; vertical-align: middle; margin: 0 4px 0 12px"></span>空
        </span>
      </div>
    </template>

    <div v-if="!loading && resp" class="grid-wrap">
      <table class="grid">
        <thead>
          <tr>
            <th class="sticky-col name-col" rowspan="2">工程师</th>
            <th class="sticky-col vendor-col" rowspan="2">Vendor</th>
            <th v-for="(d, i) in dates" :key="d"
                class="day-head"
                :class="{ weekend: weekendIdx.has(i), today: d === new Date().toISOString().slice(0,10) }">
              {{ shortDate(d) }}
            </th>
            <th class="sticky-col stat-col" rowspan="2">空 / 忙</th>
          </tr>
          <tr>
            <th v-for="(d, i) in dates" :key="d + '-dow'"
                class="dow-head"
                :class="{ weekend: weekendIdx.has(i) }">
              {{ dowLabel(d) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in sortedEngineers" :key="e.id">
            <td class="sticky-col name-col">{{ e.full_name }}</td>
            <td class="sticky-col vendor-col">{{ e.vendor_name || '—' }}</td>
            <td v-for="(d, i) in e.days" :key="d.date"
                class="day-cell"
                :class="{ busy: d.busy, weekend: weekendIdx.has(i) }">
              <el-popover v-if="d.busy" trigger="hover" placement="top" :width="260">
                <template #reference>
                  <span class="cell-fill">●</span>
                </template>
                <div>
                  <div style="font-weight: 600; margin-bottom: 4px">{{ d.date }}</div>
                  <div v-for="a in d.assignments" :key="a.id" style="font-size: 12px">
                    · {{ a.project_name }}
                  </div>
                </div>
              </el-popover>
            </td>
            <td class="sticky-col stat-col">
              <span style="color: #67c23a; font-weight: 600">{{ e.free_day_count }}</span>
              /
              <span style="color: #f56c6c">{{ e.busy_day_count }}</span>
            </td>
          </tr>
          <tr v-if="sortedEngineers.length === 0">
            <td :colspan="dayCount + 3" style="text-align: center; color: #909399; padding: 20px">
              没有工程师数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <el-skeleton v-if="loading" :rows="6" animated />
  </el-card>
</template>

<style scoped>
.grid-wrap { overflow-x: auto; }
.grid {
  border-collapse: collapse;
  font-size: 12px;
  width: max-content;
  min-width: 100%;
}
.grid th, .grid td {
  border: 1px solid #ebeef5;
  padding: 4px 6px;
  text-align: center;
  white-space: nowrap;
  background: white;
}
.day-head { font-weight: 500; color: #606266; }
.dow-head { color: #909399; font-weight: 400; font-size: 11px; }
.weekend { background: #fafafa; color: #909399; }
.today { background: #fdf6ec !important; color: #e6a23c; font-weight: 600; }

.day-cell { width: 26px; height: 28px; }
.day-cell.busy { background: #f56c6c; }
.day-cell.busy .cell-fill { color: white; cursor: pointer; }
.day-cell:not(.busy) { background: #e1f3d8; }
.cell-fill { display: inline-block; line-height: 1; font-size: 14px; }

.sticky-col {
  position: sticky;
  background: white;
  z-index: 2;
}
.name-col { left: 0; min-width: 100px; text-align: left; font-weight: 500; }
.vendor-col { left: 100px; min-width: 130px; text-align: left; color: #606266; }
.stat-col { right: 0; min-width: 80px; }
thead th.sticky-col { z-index: 3; }
</style>
