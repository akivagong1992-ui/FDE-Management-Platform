<script setup lang="ts">
import { BASE_W, BASE_H, useScale } from '@/composables/useScale'

const { scale } = useScale()
</script>

<template>
  <div class="scale-frame">
    <div
      class="scale-wrap"
      :style="{
        width: `${BASE_W}px`,
        height: `${BASE_H}px`,
        transform: `scale(${scale})`,
      }"
    >
      <router-view />
    </div>
  </div>
</template>

<style>
/* 黑底铺满，scale-wrap 居中，非 16:9 屏自然显示黑边 */
html, body, #app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background: #000;
}

.scale-frame {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  overflow: hidden;
}
.scale-wrap {
  transform-origin: center center;
  flex-shrink: 0;
  /* 1920×1080 base canvas — 所有内层 .cockpit 用 100% 填充本容器 */
}
</style>
