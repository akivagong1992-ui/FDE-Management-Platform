<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  value: number | null | undefined
  duration?: number
  decimals?: number
  formatter?: (n: number) => string
}>(), { duration: 1200, decimals: 0 })

const display = ref(0)
let raf = 0

const formatted = computed(() => {
  if (props.value == null) return '—'
  const v = display.value
  if (props.formatter) return props.formatter(v)
  return v.toLocaleString('en-HK', {
    maximumFractionDigits: props.decimals,
    minimumFractionDigits: props.decimals,
  })
})

watch(
  () => props.value,
  (newVal) => {
    if (newVal == null || isNaN(newVal)) return
    const startVal = display.value
    if (startVal === newVal) return
    const startTs = performance.now()
    cancelAnimationFrame(raf)
    const tick = (now: number) => {
      const t = Math.min((now - startTs) / props.duration, 1)
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3)
      display.value = startVal + (newVal - startVal) * eased
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
  },
  { immediate: true },
)
</script>

<template>
  <span>{{ formatted }}</span>
</template>
