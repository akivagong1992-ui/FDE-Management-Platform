import http from './http'

export interface SavingsAndValue {
  savings_from_revenue_projects: number
  value_created_from_no_revenue_projects: number
  total_c_view: number
  revenue_project_count: number
  no_revenue_project_count: number
  currency: string
}

export interface OverviewKpi {
  active_projects: number
  team_size: number
  on_time_delivery_rate: number  // 后端保留供审计；前端不再展示，改用 completed_this_month
  completed_this_month: number
  delivered_clients: string[]
  capability_by_category: { category: string; engineer_count: number }[]
  by_status: { label: string; count: number }[]
  updated_at: string
  // Legacy
  knowledge_assets?: number
  renewal_rate?: number
  certifications?: number
}

export const getOverview = () => http.get<OverviewKpi>('/overview').then((r) => r.data)
export const getSavingsAndValue = () =>
  http.get<SavingsAndValue>('/savings-and-value').then((r) => r.data)

export interface KnowledgeStats {
  total_assets: number
  by_category: { code: string; label: string; count: number }[]
  recent_30d: number
  project_coverage: number
  total_references: number
  distinct_reused_assets: number
  total_hours_saved: number
}
export const getKnowledgeStats = () =>
  http.get<KnowledgeStats>('/knowledge-stats').then((r) => r.data)

export interface GrowthTrendPoint {
  date: string
  engineer_count: number
  avg_skill_count: number
  avg_skill_level: number
  avg_cert_count: number
}
export interface GrowthTrend {
  series: GrowthTrendPoint[]
  snapshots_count: number
  growth_delta: {
    avg_skill_count: number
    avg_skill_level: number
    avg_cert_count: number
  }
}
export const getGrowthTrend = () => http.get<GrowthTrend>('/growth-trend').then((r) => r.data)

// ── Phase 3 bulk aggregation types ──────────────────────────────

export interface ProjectBoardItem {
  project_id: number; name: string; code: string | null
  kind: 'revenue' | 'no_revenue'; status: string
  district: string | null
  need_party: string | null; sales_person: string | null
  planned_start: string | null; planned_end: string | null
}
export interface ProjectBoard {
  total: number
  by_status: { label: string; count: number }[]
  by_district: { code: string; label: string; count: number }[]
  items: ProjectBoardItem[]
}
export const getProjectBoard = () => http.get<ProjectBoard>('/project-board').then((r) => r.data)

export interface ProfitCompare {
  total_savings: number; total_value_created: number; total_c_view: number
  top_savings_projects: { project_id: number; name: string; savings: number; benchmark: number; actual: number }[]
  top_value_projects: { project_id: number; name: string; value_created: number }[]
  vendor_contribution_rank: { vendor_id: number; name: string; savings: number }[]
}
export const getProfitCompare = () => http.get<ProfitCompare>('/profit-compare').then((r) => r.data)

export interface EngineerStats {
  total: number; active: number
  by_vendor: { vendor_id: number; name: string; count: number }[]
  by_level: { level: number; count: number }[]
  top_allocated: { engineer_id: number; name: string; alloc_pct: number }[]
}
export const getEngineerStats = () => http.get<EngineerStats>('/engineer-stats').then((r) => r.data)

export interface DueSoonProject {
  project_id: number; name: string; status: string
  planned_end: string; days_to_due: number; overdue: boolean
}
export interface InProgressProject {
  project_id: number; name: string; status: string
  planned_start: string | null; planned_end: string | null; overdue: boolean
}
export interface EfficiencyStats {
  // Legacy 率类字段：后端保留，前端不再展示
  total_rework_count?: number
  total_change_count?: number
  rework_rate?: number
  avg_changes_per_project?: number
  clean_delivery_count?: number
  total_projects: number; finished_with_dates: number
  on_time_count: number; on_time_rate: number
  by_status: { label: string; count: number }[]
  recent_completions: { project_id: number; name: string; planned_end: string | null; actual_end: string; on_time: boolean }[]
  // 进度看板字段
  active_count: number
  completed_this_month: number
  delivered_total: number
  due_soon_count: number
  due_soon: DueSoonProject[]
  in_progress_projects: InProgressProject[]
  today: string
}
export const getEfficiencyStats = () => http.get<EfficiencyStats>('/efficiency-stats').then((r) => r.data)

export interface CapabilityStats {
  total_certificates: number
  by_issuer: { issuer: string; count: number }[]
  skill_heatmap: { category: string; level: number; count: number }[]
  top_certified_engineers: { engineer_id: number; name: string; cert_count: number }[]
}
export const getCapabilityStats = () => http.get<CapabilityStats>('/capability-stats').then((r) => r.data)

export interface RelationshipStats {
  total_retrospectives: number
  average_satisfaction: number
  action_closure_rate: number
  renewal_rate_proxy: number
  true_renewal_rate?: number
  renewed_project_count?: number
  top_clients_by_project_count: { need_party_id: number; name: string; project_count: number }[]
  // Renewal funnel (Phase 3-next-iii Round 2)
  renewal_attempts_total?: number
  renewal_won_count?: number
  renewal_lost_count?: number
  renewal_pending_count?: number
  renewal_win_rate?: number
  renewal_lost_reasons?: { code: string; label: string; count: number }[]
}
export const getRelationshipStats = () => http.get<RelationshipStats>('/relationship-stats').then((r) => r.data)
