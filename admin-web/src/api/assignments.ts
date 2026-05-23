import http from './http'

export type AssignmentStatus = 'planned' | 'in_progress' | 'ended' | 'cancelled'

export interface Assignment {
  id: number
  engineer_id: number
  engineer_name?: string | null
  project_id: number
  project_name?: string | null
  project_code?: string | null
  role?: string | null
  allocation_ratio: number
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  status: AssignmentStatus
  notes?: string | null
  created_at: string
}

export interface AssignmentPayload {
  engineer_id: number
  project_id: number
  role?: string | null
  allocation_ratio?: number
  planned_start_date?: string | null
  planned_end_date?: string | null
  actual_start_date?: string | null
  actual_end_date?: string | null
  status?: AssignmentStatus
  notes?: string | null
}

export const listAssignments = (params?: { engineer_id?: number; project_id?: number; status_filter?: AssignmentStatus }) =>
  http.get<Assignment[]>('/assignments', { params }).then((r) => r.data)
export const createAssignment = (p: AssignmentPayload) =>
  http.post<Assignment>('/assignments', p).then((r) => r.data)
export const updateAssignment = (id: number, p: Partial<AssignmentPayload>) =>
  http.patch<Assignment>(`/assignments/${id}`, p).then((r) => r.data)
export const endAssignment = (id: number, actual_end_date?: string) =>
  http.post<Assignment>(`/assignments/${id}/end`, null, { params: actual_end_date ? { actual_end_date } : {} }).then((r) => r.data)
export const deleteAssignment = (id: number) => http.delete(`/assignments/${id}`)
