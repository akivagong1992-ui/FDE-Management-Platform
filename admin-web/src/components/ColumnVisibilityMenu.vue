<script setup lang="ts">
import { computed } from 'vue'

interface ColumnDef {
  key: string
  label: string
}

const props = defineProps<{
  columns: ColumnDef[]
  modelValue: Set<string>  // visible column keys
}>()
const emit = defineEmits<{ 'update:modelValue': [Set<string>] }>()

function toggle(key: string) {
  const next = new Set(props.modelValue)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  emit('update:modelValue', next)
}

function selectAll() {
  emit('update:modelValue', new Set(props.columns.map((c) => c.key)))
}

function clear() {
  emit('update:modelValue', new Set())
}

const hiddenCount = computed(() => props.columns.length - props.modelValue.size)
</script>

<template>
  <el-dropdown trigger="click" :hide-on-click="false">
    <el-button size="small" plain>
      <span style="font-size: 12px">显示列</span>
      <span v-if="hiddenCount > 0"
            style="color: #e6a23c; font-size: 11px; margin-left: 4px">
        ({{ hiddenCount }} 隐藏)
      </span>
      <span style="margin-left: 4px; color: #909399; font-size: 10px">▾</span>
    </el-button>
    <template #dropdown>
      <div class="col-vis-menu">
        <div class="col-vis-actions">
          <el-button link size="small" @click="selectAll">全选</el-button>
          <el-button link size="small" @click="clear">清空</el-button>
        </div>
        <div class="col-vis-list">
          <div v-for="c in columns" :key="c.key" class="col-vis-row">
            <el-checkbox :model-value="modelValue.has(c.key)" @change="toggle(c.key)">
              <span style="font-size: 13px">{{ c.label }}</span>
            </el-checkbox>
          </div>
        </div>
      </div>
    </template>
  </el-dropdown>
</template>

<style scoped>
.col-vis-menu { padding: 8px; min-width: 160px; }
.col-vis-actions {
  display: flex; justify-content: space-between;
  padding-bottom: 6px; border-bottom: 1px solid #ebeef5; margin-bottom: 6px;
}
.col-vis-list { max-height: 320px; overflow-y: auto; }
.col-vis-row { padding: 3px 0; }
</style>
