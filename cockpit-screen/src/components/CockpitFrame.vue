<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const logoSrc = '/china-telecom-logo.png'

const tabs = [
  { n: 1, path: '/overview', title: '总览' },
  { n: 2, path: '/project-map', title: '项目地图' },
  { n: 3, path: '/profit-compare', title: '利润对比 ⭐' },
  { n: 4, path: '/engineer', title: '工程师视图' },
  { n: 5, path: '/efficiency', title: '效率榜' },
  { n: 6, path: '/knowledge', title: '技术沉淀 ⭐' },
  { n: 7, path: '/capability', title: '团队能力 ⭐' },
  { n: 8, path: '/relationship', title: '客户口碑 ⭐' },
]

const activePath = computed(() => route.path)
const now = ref(new Date())
const autoPlay = ref(false)
let clockTimer: number | undefined
let playTimer: number | undefined

function go(path: string) {
  router.push(path)
}

function nextTab() {
  const idx = tabs.findIndex((t) => t.path === route.path)
  const next = tabs[(idx + 1) % tabs.length]
  router.push(next.path)
}

function toggleAutoPlay() {
  autoPlay.value = !autoPlay.value
  if (autoPlay.value) {
    playTimer = window.setInterval(nextTab, 15000)
  } else if (playTimer) {
    clearInterval(playTimer)
  }
}

onMounted(() => {
  clockTimer = window.setInterval(() => (now.value = new Date()), 1000)
})
onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (playTimer) clearInterval(playTimer)
})
</script>

<template>
  <div class="cockpit">
    <header class="header">
      <div class="header-side">
        <img
          :src="logoSrc"
          alt="中国电信"
          class="logo"
          @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
        />
        <span class="brand glow-text">交付团队驾驶舱</span>
        <span class="subtitle">中国电信国际香港分公司</span>
      </div>
      <div class="header-center">
        <span class="time">{{ now.toLocaleString('zh-CN', { hour12: false }) }}</span>
      </div>
      <div class="header-side right">
        <button class="btn" @click="toggleAutoPlay">
          {{ autoPlay ? '⏸ 暂停轮播' : '▶ 自动轮播' }}
        </button>
      </div>
    </header>

    <nav class="tabs">
      <button
        v-for="t in tabs"
        :key="t.path"
        :class="['tab', activePath === t.path ? 'active' : '']"
        @click="go(t.path)"
      >
        <span class="tab-n">{{ String(t.n).padStart(2, '0') }}</span>
        <span class="tab-title">{{ t.title }}</span>
      </button>
    </nav>

    <main class="body">
      <router-view v-slot="{ Component }">
        <transition name="tab-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.cockpit {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background:
    radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.08), transparent 40%),
    var(--cockpit-bg);
}
.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--cockpit-border);
}
.header-side { flex: 1; display: flex; align-items: center; gap: 14px; }
.header-side.right { justify-content: flex-end; }
.logo { height: 38px; width: auto; object-fit: contain; filter: brightness(1.1); }
.header-center { flex: 0 0 auto; }
.brand { font-size: 22px; font-weight: 700; letter-spacing: 4px; }
.subtitle { color: var(--cockpit-text-dim); font-size: 13px; letter-spacing: 2px; }
.time { font-family: 'Courier New', monospace; font-size: 18px; color: var(--cockpit-accent); }
.btn {
  background: transparent;
  color: var(--cockpit-accent);
  border: 1px solid var(--cockpit-border);
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
}
.btn:hover { background: rgba(0, 229, 255, 0.1); }

.tabs {
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--cockpit-border);
}
.tab {
  flex: 1;
  background: transparent;
  border: 1px solid transparent;
  color: var(--cockpit-text-dim);
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.2s;
}
.tab:hover { color: var(--cockpit-text); border-color: var(--cockpit-border); }
.tab.active {
  color: var(--cockpit-accent);
  background: rgba(0, 229, 255, 0.08);
  border-color: var(--cockpit-accent);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.3);
}
.tab-n {
  font-family: 'Courier New', monospace;
  font-weight: bold;
  font-size: 16px;
  opacity: 0.7;
}
.tab-title { letter-spacing: 1px; }

.body {
  flex: 1;
  padding: 16px 24px;
  overflow: hidden;
}
</style>
