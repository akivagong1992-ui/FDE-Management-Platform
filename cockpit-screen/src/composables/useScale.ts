/**
 * Big-screen scale composable — 大屏 dashboard 通用做法。
 *
 * 设计画布固定 1920×1080，整个驾驶舱用 transform: scale 等比缩放到任意视窗。
 *
 * 4K (3840×2160 / 85") → scale = 2，元素物理大小 ×2
 * 笔记本 (例 1440×900) → scale = 0.75
 *
 * 等比缩放 (取短边 fit)，避免拉伸变形；非 16:9 屏幕在 wrapper 外侧居中留黑边。
 */
import { onMounted, onUnmounted, ref } from 'vue'

export const BASE_W = 1920
export const BASE_H = 1080

export function useScale() {
  const scale = ref(1)

  function update() {
    const sw = window.innerWidth
    const sh = window.innerHeight
    scale.value = Math.min(sw / BASE_W, sh / BASE_H)
  }

  onMounted(() => {
    update()
    window.addEventListener('resize', update)
  })
  onUnmounted(() => {
    window.removeEventListener('resize', update)
  })

  return { scale }
}
