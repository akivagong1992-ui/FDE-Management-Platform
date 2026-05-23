import http from './http'

export type RevenueStatus = 'pending' | 'received' | 'written_off'

export interface ProjectRevenue {
  id: number
  project_id: number
  project_name?: string | null
  amount: number | string                  // 团队入账（pass-through 到 Vendor）
  gross_amount?: number | string | null    // 客户付款总额（销售切除前）
  currency: string
  recognized_date: string
  invoice_no?: string | null
  description?: string | null
  status: RevenueStatus
  received_at?: string | null
  created_at: string
}

export interface RevenuePayload {
  project_id: number
  amount: number
  gross_amount?: number | null
  currency?: string
  recognized_date: string
  invoice_no?: string | null
  description?: string | null
  status?: RevenueStatus
}

export const listRevenues = (params?: { project_id?: number; status_filter?: RevenueStatus }) =>
  http.get<ProjectRevenue[]>('/project-revenues', { params }).then((r) => r.data)
export const createRevenue = (p: RevenuePayload) =>
  http.post<ProjectRevenue>('/project-revenues', p).then((r) => r.data)
export const updateRevenue = (id: number, p: Partial<RevenuePayload>) =>
  http.patch<ProjectRevenue>(`/project-revenues/${id}`, p).then((r) => r.data)
export const deleteRevenue = (id: number) => http.delete(`/project-revenues/${id}`)
