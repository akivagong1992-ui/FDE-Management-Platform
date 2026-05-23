import http from './http'

export interface Retrospective {
  id: number
  project_id: number
  project_name?: string | null
  satisfaction_score: number
  what_went_well?: string | null
  what_to_improve?: string | null
  action_items?: string | null
  next_review_date?: string | null
  is_closed: boolean
  created_by_user_id?: number | null
  created_at: string
  updated_at: string
}

export interface RetrospectivePayload {
  project_id: number
  satisfaction_score: number
  what_went_well?: string | null
  what_to_improve?: string | null
  action_items?: string | null
  next_review_date?: string | null
  is_closed?: boolean
}

export const listRetros = (params?: { project_id?: number; is_closed?: boolean }) =>
  http.get<Retrospective[]>('/retrospectives', { params }).then((r) => r.data)
export const createRetro = (p: RetrospectivePayload) =>
  http.post<Retrospective>('/retrospectives', p).then((r) => r.data)
export const updateRetro = (id: number, p: Partial<RetrospectivePayload>) =>
  http.patch<Retrospective>(`/retrospectives/${id}`, p).then((r) => r.data)
export const deleteRetro = (id: number) => http.delete(`/retrospectives/${id}`)
