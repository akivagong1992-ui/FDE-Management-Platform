<script setup lang="ts">
import { computed, ref } from 'vue'

type FilterValue = string | number

const props = defineProps<{
  options: FilterValue[]              // distinct values to choose from
  modelValue: Set<FilterValue>        // selected values (empty = no filter)
  width?: number
}>()
const emit = defineEmits<{ 'update:modelValue': [Set<FilterValue>] }>()

const search = ref('')

const filteredOptions = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.options
  return props.options.filter((o) => String(o ?? '').toLowerCase().includes(q))
})

function toggle(val: FilterValue) {
  const next = new Set(props.modelValue)
  if (next.has(val)) next.delete(val)
  else next.add(val)
  emit('update:modelValue', next)
}

function selectAllFiltered() {
  const next = new Set(props.modelValue)
  filteredOptions.value.forEach((v) => next.add(v))
  emit('update:modelValue', next)
}

function clearFilter() {
  emit('update:modelValue', new Set())
  search.value = ''
}

const hasActive = computed(() => props.modelValue.size > 0)
const activeCount = computed(() => props.modelValue.size)
</script>

<template>
  <el-popover :width="width ?? 220" trigger="click" placement="bottom-start"
              popper-style="padding: 8px">
    <template #reference>
      <span class="filter-trigger" :class="{ active: hasActive }">
        <span v-if="hasActive" class="badge">{{ activeCount }}</span>
        <span v-else>▾</span>
      </span>
    </template>
    <div>
      <el-input v-model="search" placeholder="搜索..." size="small" clearable
                style="margin-bottom: 8px" />
      <div class="filter-list">
        <div v-if="!filteredOptions.length" class="filter-empty">无匹配选项</div>
        <div v-for="opt in filteredOptions" :key="String(opt)" class="filter-row">
          <el-checkbox :model-value="modelValue.has(opt)" @change="toggle(opt)">
            <span class="filter-opt-text">
              {{ opt === null || opt === '' ? '（空）' : opt }}
            </span>
          </el-checkbox>
        </div>
      </div>
      <div class="filter-actions">
        <el-button link size="small" @click="clearFilter">清空</el-button>
        <el-button link type="primary" size="small" @click="selectAllFiltered">
          全选{{ search ? '(过滤后)' : '' }}
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<style scoped>
.filter-trigger {
  margin-left: 6px; cursor: pointer;
  color: #909399; font-size: 12px;
  display: inline-flex; align-items: center; justify-content: center;
  user-select: none;
  width: 18px; height: 18px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  background: #fff;
  vertical-align: middle;
  transition: all 0.15s;
}
.filter-trigger:hover {
  color: #409eff; border-color: #409eff; background: #ecf5ff;
}
.filter-trigger.active {
  color: white; background: #409eff; border-color: #409eff;
  font-weight: 600;
  width: auto; padding: 0 5px; min-width: 18px;
}
.badge {
  font-size: 10px; line-height: 1; min-width: 12px; text-align: center;
}
.filter-list {
  max-height: 220px; overflow-y: auto;
  border-top: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5;
  padding: 4px 0;
}
.filter-empty {
  text-align: center; color: #c0c4cc;
  padding: 12px; font-size: 12px;
}
.filter-row { padding: 2px 4px; }
.filter-opt-text { font-size: 12px; }
.filter-actions {
  display: flex; justify-content: space-between;
  margin-top: 6px;
}
</style>
