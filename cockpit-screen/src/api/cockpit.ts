import http from './http'

export interface SavingsAndValue {
  savings_from_revenue_projects: number
  value_created_from_no_revenue_projects: number
  total_c_view: number
  revenue_project_count: number
  no_revenue_project_count: number
  currency: string
}

export interface ShowcaseClient {
  name: string
  logo_path: string | null
}
export interface OverviewKpi {
  active_projects: number
  team_size: number
  on_time_delivery_rate: number  // 后端保留供审计；前端不再展示，改用 completed_this_month
  completed_this_month: number
  showcase_clients: ShowcaseClient[]
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

// D 限定版（口径 D · 公司毛利率提升）— 仅 3 个百分率 + 项目数
// 刻意不暴露 gross / team_revenue / non_service / benchmark 等绝对金额
export interface MarginLiftPct {
  outsource_margin_pct: number
  fde_margin_pct: number
  margin_lift_pct: number
  counted_projects: number
  unit: string
}
export const getMarginLiftPct = () =>
  http.get<MarginLiftPct>('/margin-lift-pct').then((r) => r.data)

export interface RecentAsset {
  id: number
  title: string
  category_code: string
  category_label: string
  project_name: string | null
  created_at: string | null
}
export interface KnowledgeStats {
  total_assets: number
  by_category: { code: string; label: string; count: number }[]
  recent_30d: number
  project_coverage: number
  total_references: number
  distinct_reused_assets: number
  total_hours_saved: number
  recent_assets: RecentAsset[]
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
  total_certificates: number  // 替代旧 by_level（按 engineer.level L1-L3 聚合）
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
  // 新口径: cert_level (L1/L2/L3) × cert_category → distinct engineer count
  cert_heatmap: { category: string; level: 'L1' | 'L2' | 'L3'; count: number }[]
  top_certified_engineers: { engineer_id: number; name: string; cert_count: number }[]
}
export const getCapabilityStats = () => http.get<CapabilityStats>('/capability-stats').then((r) => r.data)

