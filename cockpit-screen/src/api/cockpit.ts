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
  on_time_delivery_rate: number
  knowledge_assets: number
  renewal_rate: number
  certifications: number
  updated_at: string
  // Phase 2b — these mock fields are gradually replaced by real ones
  cumulative_margin_hkd?: number  // (kept for backward-compat; replaced by C-tier)
  outsource_saving_hkd?: number
}

export const getOverview = () => http.get<OverviewKpi>('/overview').then((r) => r.data)
export const getSavingsAndValue = () =>
  http.get<SavingsAndValue>('/savings-and-value').then((r) => r.data)
