import http from './http'

export type RenewalOutcome = 'pending' | 'won' | 'lost'
export type LostReason =
  | 'lost_to_outsource' | 'price' | 'quality'
  | 'no_budget' | 'internal_hire' | 'other'

export const LOST_REASON_LABELS: Record<LostReason, string> = {
  lost_to_outsource: '输给传统外包',
  price: '价格因素',
  quality: '质量 / 满意度',
  no_budget: '客户无预算',
  internal_hire: '客户自建团队',
  other: '其他',
}

export interface RenewalAttempt {
  id: number
  previous_project_id: number
  previous_project_name?: string | null
  attempt_date: string
  outcome: RenewalOutcome
  won_project_id?: number | null
  won_project_name?: string | null
  lost_reason?: LostReason | null
  lost_reason_note?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface RenewalAttemptPayload {
  previous_project_id: number
  attempt_date: string
  outcome: RenewalOutcome
  won_project_id?: number | null
  lost_reason?: LostReason | null
  lost_reason_note?: string | null
  notes?: string | null
}

export const listAttempts = (outcome?: RenewalOutcome) =>
  http.get<RenewalAttempt[]>('/renewal-attempts', { params: { outcome } }).then((r) => r.data)
export const createAttempt = (p: RenewalAttemptPayload) =>
  http.post<RenewalAttempt>('/renewal-attempts', p).then((r) => r.data)
export const updateAttempt = (id: number, p: Partial<RenewalAttemptPayload>) =>
  http.patch<RenewalAttempt>(`/renewal-attempts/${id}`, p).then((r) => r.data)
export const deleteAttempt = (id: number) => http.delete(`/renewal-attempts/${id}`)
