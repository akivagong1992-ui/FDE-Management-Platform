<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listEngineers, type Engineer, type EngineerSkillRow } from '@/api/engineers'

const engineers = ref<Engineer[]>([])
const loading = ref(false)
const filterText = ref('')

async function load() {
  loading.value = true
  try {
    engineers.value = await listEngineers({ status_filter: 'active' })
  } finally {
    loading.value = false
  }
}

// 按 vendor 然后 full_name 排序，过滤：搜工程师名 / vendor / 认证名
const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  const list = engineers.value.slice().sort((a, b) => {
    const va = (a.vendor_name || '').localeCompare(b.vendor_name || '')
    return va !== 0 ? va : a.full_name.localeCompare(b.full_name)
  })
  if (!q) return list
  return list.filter((e) =>
    e.full_name.toLowerCase().includes(q)
    || (e.vendor_name || '').toLowerCase().includes(q)
    || e.skills.some((s) => s.skill_name.toLowerCase().includes(q)
                          || (s.skill_issuer || '').toLowerCase().includes(q)),
  )
})

const totalSkillAssignments = computed(() =>
  engineers.value.reduce((sum, e) => sum + e.skills.length, 0),
)

// 按 category 分组某工程师的 skills，便于展示
function groupByCategory(skills: EngineerSkillRow[]): Record<string, EngineerSkillRow[]> {
  const grouped: Record<string, EngineerSkillRow[]> = {}
  for (const s of skills) {
    const cat = s.skill_category || '其他'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(s)
  }
  // 每组内按等级降序（L3 → L1）
  for (const cat in grouped) {
    grouped[cat].sort((a, b) => (b.skill_level || '').localeCompare(a.skill_level || ''))
  }
  return grouped
}

function levelTagType(level?: string | null): 'success' | 'warning' | 'info' {
  if (level === 'L3') return 'success'
  if (level === 'L2') return 'warning'
  return 'info'
}

onMounted(load)
</script>

<template>
  <div class="cap-page" v-loading="loading">
    <!-- 顶部 stats + 操作 -->
    <div class="stats-bar">
      <div class="stats">
        <span><strong>{{ engineers.length }}</strong> 位在职工程师</span>
        <span class="sep">·</span>
        <span>共持有 <strong>{{ totalSkillAssignments }}</strong> 条认证</span>
      </div>
      <div class="ops">
        <el-input v-model="filterText" placeholder="搜工程师名 / vendor / 认证名" clearable size="small"
                  style="width: 280px" />
      </div>
    </div>

    <!-- 工程师 × 认证清单 -->
    <div v-if="filtered.length === 0" class="empty-state">
      {{ engineers.length === 0 ? '暂无在职工程师' : '没有匹配的工程师 / 认证' }}
    </div>
    <div v-else class="eng-list">
      <el-card v-for="e in filtered" :key="e.id" class="eng-card" shadow="never">
        <div class="eng-head">
          <div class="eng-name-block">
            <span class="eng-name">{{ e.full_name }}</span>
            <span class="eng-meta">{{ e.vendor_name }}</span>
          </div>
          <span class="eng-count">{{ e.skills.length }} 条认证</span>
        </div>

        <div v-if="e.skills.length === 0" class="no-skill">未挂载任何认证</div>
        <div v-else class="skill-groups">
          <div v-for="(items, cat) in groupByCategory(e.skills)" :key="cat" class="skill-group">
            <span class="cat-label">{{ cat }}</span>
            <div class="skill-tags">
              <el-tag v-for="s in items" :key="s.id" :type="levelTagType(s.skill_level)" size="default"
                      style="margin-right: 6px; margin-bottom: 4px">
                <span style="font-weight: 600">{{ s.skill_level || '—' }}</span>
                <span style="margin: 0 4px; color: #c0c4cc">|</span>
                {{ s.skill_name }}
                <span v-if="s.skill_issuer" style="margin-left: 6px; color: #909399; font-size: 11px">
                  {{ s.skill_issuer }}
                </span>
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.cap-page { display: flex; flex-direction: column; gap: 12px; }

.stats-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 4px 12px; border-bottom: 1px solid #ebeef5;
}
.stats { color: #606266; font-size: 14px; }
.stats strong { color: #303133; font-size: 16px; margin: 0 2px; }
.sep { margin: 0 8px; color: #c0c4cc; }
.ops { display: flex; gap: 8px; align-items: center; }

.empty-state {
  padding: 60px 0; text-align: center; color: #909399; font-size: 14px;
}

.eng-list { display: flex; flex-direction: column; gap: 12px; }
.eng-card { border: 1px solid #ebeef5; }
.eng-card :deep(.el-card__body) { padding: 14px 18px; }

.eng-head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 10px;
}
.eng-name { font-weight: 600; color: #303133; font-size: 15px; }
.eng-meta { color: #909399; font-size: 12px; margin-left: 10px; }
.eng-count { color: #606266; font-size: 12px; }

.no-skill { color: #c0c4cc; font-size: 13px; padding: 4px 0; }

.skill-groups { display: flex; flex-direction: column; gap: 8px; }
.skill-group { display: flex; align-items: flex-start; gap: 10px; }
.cat-label {
  min-width: 80px; padding-top: 4px;
  color: #909399; font-size: 12px; font-weight: 500;
}
.skill-tags { flex: 1; }
</style>
