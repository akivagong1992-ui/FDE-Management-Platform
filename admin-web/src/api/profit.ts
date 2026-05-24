import http from './http'

export interface OverallProfit {
  total_revenue: number
  total_vendor_service_fees: number
  total_external_expenses: number
  team_margin: number
  currency: string
}

export interface ProjectMarginRow {
  project_id: number
  project_name: string
  project_code?: string | null
  kind: 'revenue' | 'no_revenue'
  status: string
  sales_person_id: number
  sales_person_name?: string | null
  need_party_id: number
  need_party_name?: string | null
  revenue: number
  cost: number
  margin: number
}

export interface BySalesRow {
  sales_person_id: number
  sales_person_name?: string | null
  project_count: number
  revenue: number
  cost: number
  margin: number
  projects: ProjectMarginRow[]
}

export interface ByNeedPartyRow {
  need_party_id: number
  need_party_name?: string | null
  project_count: number
  revenue: number
  cost: number
  margin: number
  projects: ProjectMarginRow[]
}

export interface MarginLift {
  counted_projects: number
  total_gross_revenue: number
  total_team_revenue: number
  total_outsource_benchmark: number
  total_actual_cost: number
  total_non_service_expense: number
  outsource_margin: number
  fde_margin: number
  outsource_margin_pct: number
  fde_margin_pct: number
  margin_lift_pct: number
  extra_profit: number
  currency: string
}

export const getOverall = () => http.get<OverallProfit>('/profit/overall').then((r) => r.data)
export const getPerProject = () => http.get<ProjectMarginRow[]>('/profit/per-project').then((r) => r.data)
export const getBySalesPerson = () => http.get<BySalesRow[]>('/profit/by-sales-person').then((r) => r.data)
export const getByNeedParty = () => http.get<ByNeedPartyRow[]>('/profit/by-need-party').then((r) => r.data)
export const getMarginLift = () => http.get<MarginLift>('/profit/margin-lift').then((r) => r.data)
