import http from './http'

export type IDPStatus = 'draft' | 'in_progress' | 'completed' | 'cancelled'

export interface IDP {
  id: number
  engineer_id: number
  engineer_name?: string | null
  title: string
  target_skills?: string | null
  target_certs?: string | null
  plan_actions?: string | null
  due_date?: string | null
  status: IDPStatus
  mentor_user_id?: number | null
  created_at: string
  updated_at: string
}

export interface IDPPayload {
  engineer_id: number
  title: string
  target_skills?: string | null
  target_certs?: string | null
  plan_actions?: string | null
  due_date?: string | null
  status?: IDPStatus
  mentor_user_id?: number | null
}

export const listIDPs = (params?: { engineer_id?: number; status_filter?: IDPStatus }) =>
  http.get<IDP[]>('/idps', { params }).then((r) => r.data)
export const createIDP = (p: IDPPayload) =>
  http.post<IDP>('/idps', p).then((r) => r.data)
export const updateIDP = (id: number, p: Partial<IDPPayload>) =>
  http.patch<IDP>(`/idps/${id}`, p).then((r) => r.data)
export const deleteIDP = (id: number) => http.delete(`/idps/${id}`)
