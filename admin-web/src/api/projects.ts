import http from './http'

export type ProjectKind = 'revenue' | 'no_revenue'
export type ProjectStatus = 'drafting' | 'in_progress' | 'accepting' | 'archived' | 'cancelled'
export type BidOutcome = 'pending' | 'won' | 'lost' | 'escaped'

export const BID_OUTCOME_LABELS: Record<BidOutcome, string> = {
  pending: '投标中 / 未定',
  won: '已中标',
  lost: '已丢标',
  escaped: '中标后跑单',
}
export const BID_OUTCOME_TYPES: Record<BidOutcome, 'info' | 'success' | 'danger' | 'warning'> = {
  pending: 'info',
  won: 'success',
  lost: 'danger',
  escaped: 'warning',
}
export type ValueBasis = 'outsource_equiv' | 'other'
export type TransferReason = 'resignation' | 'role_change' | 'other'

export type HKDistrict = 'HK_ISLAND' | 'KOWLOON' | 'NT_EAST' | 'NT_WEST' | 'OUTLYING'

export const DISTRICT_LABELS: Record<HKDistrict, string> = {
  HK_ISLAND: '港岛', KOWLOON: '九龙', NT_EAST: '新界东',
  NT_WEST: '新界西', OUTLYING: '离岛',
}

export type BenchmarkBasis = 'vendor_quote' | 'historical_avg'

export const BENCHMARK_BASIS_LABELS: Record<BenchmarkBasis, string> = {
  vendor_quote: '外部供应商真实报价',
  historical_avg: '同类历史项目均价',
}

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
  contact_engineer_id?: number | null
  contact_engineer_name?: string | null
  kind: ProjectKind
  outsource_benchmark_amount?: number | string | null
  value_created_basis?: ValueBasis | null
  value_created_note?: string | null
  value_created_computed?: number | string | null
  status: ProjectStatus
  bid_outcome: BidOutcome
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  summary?: string | null
  description?: string | null
  district?: HKDistrict | null
  rework_count?: number
  change_count?: number
  renewal_of_project_id?: number | null
  benchmark_basis?: BenchmarkBasis | null
  benchmark_basis_note?: string | null
  created_at: string
  updated_at: string
}

export interface ProjectPayload {
  code?: string | null
  name: string
  need_party_id: number
  sales_person_id: number
  pm_user_id?: number | null
  contact_engineer_id?: number | null
  kind: ProjectKind
  outsource_benchmark_amount?: number | null
  value_created_basis?: ValueBasis | null
  value_created_note?: string | null
  status?: ProjectStatus
  bid_outcome?: BidOutcome
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  summary?: string | null
  description?: string | null
  district?: HKDistrict | null
  rework_count?: number
  change_count?: number
  renewal_of_project_id?: number | null
  benchmark_basis?: BenchmarkBasis | null
  benchmark_basis_note?: string | null
}

export interface ProjectComment {
  id: number
  project_id: number
  author_user_id: number
  author_role: string
  author_name?: string | null
  body: string
  created_at: string
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

export const listProjectComments = (id: number) =>
  http.get<ProjectComment[]>(`/projects/${id}/comments`).then((r) => r.data)
export const createProjectComment = (id: number, body: string) =>
  http.post<ProjectComment>(`/projects/${id}/comments`, { body }).then((r) => r.data)
export const deleteProjectComment = (projectId: number, commentId: number) =>
  http.delete(`/projects/${projectId}/comments/${commentId}`)
