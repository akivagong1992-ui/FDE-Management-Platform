import http from './http'

export interface DictItem {
  id: number
  category: string
  code: string
  label: string
  sort_order: number
  is_active: boolean
}

export const listDict = (category: string) =>
  http.get<DictItem[]>('/data-dict', { params: { category } }).then((r) => r.data)
