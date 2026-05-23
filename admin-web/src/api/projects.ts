import http from './http'

export type ProjectKind = 'revenue' | 'no_revenue'
export type ProjectStatus = 'drafting' | 'in_progress' | 'accepting' | 'closing' | 'archived'
export type ValueBasis =
  | 'outsource_equiv' | 'replace_audit_fee' | 'avoid_penalty'
  | 'save_hours' | 'strategic_reserve' | 'other'
export type TransferReason = 'resignation' | 'role_change' | 'other'

export interface Project {
  id: number
  code?: string | null
  name: string
  need_party_id: number
  need_party_name?: string | null
  sales_person_id: number
  sales_person_name?: string | null
  sales_person_active?: boolean | null
  pm_user_id?: number | null
  kind: ProjectKind
  outsource_benchmark_amount?: number | string | null
  value_created_basis?: ValueBasis | null
  value_created_note?: string | null
  value_created_computed?: number | string | null
  status: ProjectStatus
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  description?: string | null
  created_at: string
  updated_at: string
}

export interface ProjectPayload {
  code?: string | null
  name: string
  need_party_id: number
  sales_person_id: number
  pm_user_id?: number | null
  kind: ProjectKind
  outsource_benchmark_amount?: number | null
  value_created_basis?: ValueBasis | null
  value_created_note?: string | null
  status?: ProjectStatus
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  description?: string | null
}

export interface TransferLog {
  id: number
  project_id: number
  from_sales_person_id: number
  to_sales_person_id: number
  reason: TransferReason
  reason_note?: string | null
  operator_user_id?: number | null
  created_at: string
}

export const listProjects = (params?: { kind?: ProjectKind; status_filter?: ProjectStatus; sales_person_id?: number; need_party_id?: number }) =>
  http.get<Project[]>('/projects', { params }).then((r) => r.data)
export const getProject = (id: number) => http.get<Project>(`/projects/${id}`).then((r) => r.data)
export const createProject = (p: ProjectPayload) =>
  http.post<Project>('/projects', p).then((r) => r.data)
export const updateProject = (id: number, p: Partial<ProjectPayload>) =>
  http.patch<Project>(`/projects/${id}`, p).then((r) => r.data)
export const deleteProject = (id: number) => http.delete(`/projects/${id}`)
export const transferSales = (
  id: number,
  payload: { to_sales_person_id: number; reason: TransferReason; reason_note?: string },
) => http.post<Project>(`/projects/${id}/transfer-sales`, payload).then((r) => r.data)
export const listTransferLogs = (id: number) =>
  http.get<TransferLog[]>(`/projects/${id}/transfer-logs`).then((r) => r.data)
