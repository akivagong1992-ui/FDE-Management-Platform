// 全站统一金额 / 数字格式化。所有 HK$ 金额一律 2 位小数 + en-HK 千分位。
// 不要在 view 里再写本地 fmt2 / toLocaleString，直接 import 这里。

type Numlike = number | string | null | undefined

/** 2 位小数 + 千分位（en-HK 标准记法）。空 / 非数 → "—"。
 *  仅返回数字部分，不带 "HK$" 前缀（前缀放在 template 里，便于样式控制）。*/
export function fmt2(n: Numlike): string {
  if (n == null || n === '') return '—'
  const v = Number(n)
  if (!Number.isFinite(v)) return '—'
  return new Intl.NumberFormat('en-HK', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v)
}

/** 整数千分位。用于人数 / 项目数 / 工时等。*/
export function fmtInt(n: Numlike): string {
  if (n == null || n === '') return '—'
  const v = Number(n)
  if (!Number.isFinite(v)) return '—'
  return new Intl.NumberFormat('en-HK', { maximumFractionDigits: 0 }).format(v)
}

/** 万元单位（驾驶舱 / Home KPI 大数字用）。n = 12345 → "1.2"。*/
export function fmtWan(n: Numlike, digits = 1): string {
  if (n == null || n === '') return '—'
  const v = Number(n)
  if (!Number.isFinite(v)) return '—'
  return (v / 10000).toLocaleString('en-HK', { maximumFractionDigits: digits })
}

/** "HK$ 12,345.67"。少数地方需要完整字符串时用。*/
export function formatHKD(n: Numlike): string {
  return `HK$ ${fmt2(n)}`
}
