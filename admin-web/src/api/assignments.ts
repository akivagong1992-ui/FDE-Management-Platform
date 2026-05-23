import http from './http'

export type AssignmentStatus = 'planned' | 'in_progress' | 'ended' | 'cancelled'
export type ApprovalStatus = 'pending' | 'accepted' | 'rejected'
export type MessageKind = 'system' | 'pm' | 'engineer'

export const APPROVAL_LABEL: Record<ApprovalStatus, string> = {
  pending: '待工程师确认', accepted: '已接单', rejected: '已拒单',
}
export const APPROVAL_TAG_TYPE: Record<ApprovalStatus, 'warning' | 'success' | 'danger'> = {
  pending: 'warning', accepted: 'success', rejected: 'danger',
}

export interface Assignment {
  id: number
  engineer_id: number
  engineer_name?: string | null
  project_id: number
  project_name?: string | null
  project_code?: string | null
  role?: string | null
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  status: AssignmentStatus
  approval_status: ApprovalStatus
  engineer_responded_at?: string | null
  created_by_user_id?: number | null
  message_count: number
  notes?: string | null
  created_at: string
}

export interface AssignmentPayload {
  engineer_id: number
  project_id: number
  role?: string | null
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  status?: AssignmentStatus
  notes?: string | null
  initial_message?: string | null
}

export interface AssignmentMessage {
  id: number
  sender_user_id: number | null
  sender_name: string | null
  sender_kind: MessageKind
  body: string
  created_at: string
}

export const listAssignments = (params?: {
  engineer_id?: number
  project_id?: number
  status_filter?: AssignmentStatus
  approval_filter?: ApprovalStatus
}) =>
  http.get<Assignment[]>('/assignments', { params }).then((r) => r.data)

export const createAssignment = (p: AssignmentPayload) =>
  http.post<Assignment>('/assignments', p).then((r) => r.data)
export const updateAssignment = (id: number, p: Partial<AssignmentPayload>) =>
  http.patch<Assignment>(`/assignments/${id}`, p).then((r) => r.data)
export const endAssignment = (id: number, actual_end_date?: string) =>
  http.post<Assignment>(`/assignments/${id}/end`, null, {
    params: actual_end_date ? { actual_end_date } : {},
  }).then((r) => r.data)
export const deleteAssignment = (id: number) => http.delete(`/assignments/${id}`)

export const acceptAssignment = (id: number, note?: string) =>
  http.post<Assignment>(`/assignments/${id}/accept`, { note: note || null }).then((r) => r.data)
export const rejectAssignment = (id: number, reason: string) =>
  http.post<Assignment>(`/assignments/${id}/reject`, { reason }).then((r) => r.data)

export const listMessages = (id: number) =>
  http.get<AssignmentMessage[]>(`/assignments/${id}/messages`).then((r) => r.data)
export const addMessage = (id: number, body: string) =>
  http.post<AssignmentMessage>(`/assignments/${id}/messages`, { body }).then((r) => r.data)
