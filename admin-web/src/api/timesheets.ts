import http from './http'

export type SlotCode = 'morning' | 'afternoon' | 'evening'
export const SLOT_LABEL: Record<SlotCode, string> = {
  morning: '上午', afternoon: '下午', evening: '晚上',
}

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'
export const APPROVAL_LABEL: Record<ApprovalStatus, string> = {
  pending: '待审', approved: '已审', rejected: '已拒',
}
export const APPROVAL_TAG_TYPE: Record<ApprovalStatus, 'warning' | 'success' | 'danger'> = {
  pending: 'warning', approved: 'success', rejected: 'danger',
}

export interface Timesheet {
  id: number
  engineer_id: number
  engineer_name?: string | null
  project_id: number
  project_name?: string | null
  assignment_id?: number | null
  work_date: string
  has_morning: boolean
  has_afternoon: boolean
  has_evening: boolean
  is_workday: boolean
  natural_days: number | string
  weighted_days: number | string
  description?: string | null
  approval_status: ApprovalStatus
  reject_reason?: string | null
  reviewed_at?: string | null
  submitted_by_user_id?: number | null
  is_approved: boolean  // legacy mirror of approval_status === 'approved'
  created_at: string
}

export interface TimesheetPayload {
  engineer_id: number
  project_id: number
  assignment_id?: number | null
  work_date: string
  has_morning: boolean
  has_afternoon: boolean
  has_evening: boolean
  description?: string | null
}

export interface TimesheetRangePayload {
  engineer_id: number
  project_id: number
  assignment_id?: number | null
  start_date: string
  end_date: string
  slots: SlotCode[]
  description?: string | null
}

export interface ImportResult {
  created: number
  skipped: number
  errors: { row: number; message: string }[]
}

export interface TimesheetRangeResult {
  created: Timesheet[]
  skipped: { row: number; message: string }[]
  total_natural_days: number | string
  total_weighted_days: number | string
}

export const listTimesheets = (params?: {
  engineer_id?: number; project_id?: number; date_from?: string; date_to?: string
}) =>
  http.get<Timesheet[]>('/timesheets', { params }).then((r) => r.data)

export const createTimesheet = (p: TimesheetPayload) =>
  http.post<Timesheet>('/timesheets', p).then((r) => r.data)

export const createTimesheetRange = (p: TimesheetRangePayload) =>
  http.post<TimesheetRangeResult>('/timesheets/range', p).then((r) => r.data)

export const updateTimesheet = (
  id: number,
  p: Partial<Omit<TimesheetPayload, 'engineer_id' | 'project_id' | 'work_date'>> & { is_workday?: boolean },
) =>
  http.patch<Timesheet>(`/timesheets/${id}`, p).then((r) => r.data)

export const deleteTimesheet = (id: number) => http.delete(`/timesheets/${id}`)

export const approveTimesheet = (id: number) =>
  http.patch<Timesheet>(`/timesheets/${id}/approve`).then((r) => r.data)

export const rejectTimesheet = (id: number, reason: string) =>
  http.patch<Timesheet>(`/timesheets/${id}/reject`, { reason }).then((r) => r.data)

export const listTimesheetsByApproval = (status: ApprovalStatus) =>
  http.get<Timesheet[]>('/timesheets', { params: { approval_filter: status } }).then((r) => r.data)

export async function downloadTemplate(): Promise<void> {
  const resp = await http.get('/timesheets/template', { responseType: 'blob' })
  const blob = new Blob([resp.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'timesheet-template.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export async function importExcel(file: File): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await http.post<ImportResult>('/timesheets/import-excel', form)
  return data
}

// 香港工时计算工具（前端实时预览用，与后端 compute_weighted_days 保持一致）
export function isHkWorkday(dateStr: string): boolean {
  const d = new Date(dateStr + 'T00:00:00')
  const w = d.getDay()  // 0=Sun..6=Sat
  return w >= 1 && w <= 5
}

export function computePreview(startDate: string, endDate: string, slots: SlotCode[]):
  { days: number; natural: number; weighted: number } {
  if (!startDate || !endDate || slots.length === 0) return { days: 0, natural: 0, weighted: 0 }
  const start = new Date(startDate + 'T00:00:00').getTime()
  const end = new Date(endDate + 'T00:00:00').getTime()
  if (end < start) return { days: 0, natural: 0, weighted: 0 }
  const hasM = slots.includes('morning')
  const hasA = slots.includes('afternoon')
  const hasE = slots.includes('evening')
  let natural = 0, weighted = 0, days = 0
  for (let t = start; t <= end; t += 86400000) {
    days += 1
    const d = new Date(t)
    const w = d.getDay()
    const isWd = w >= 1 && w <= 5
    const dayMul = isWd ? 1.0 : 1.5
    if (hasM) { natural += 0.5; weighted += 0.5 * dayMul }
    if (hasA) { natural += 0.5; weighted += 0.5 * dayMul }
    if (hasE) { natural += 0.5; weighted += 0.5 * 1.5 }
  }
  return { days, natural: round2(natural), weighted: round2(weighted) }
}
function round2(n: number): number { return Math.round(n * 100) / 100 }
