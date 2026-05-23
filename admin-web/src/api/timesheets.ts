import http from './http'

export interface Timesheet {
  id: number
  engineer_id: number
  engineer_name?: string | null
  project_id: number
  project_name?: string | null
  assignment_id?: number | null
  work_date: string
  person_days: number | string
  description?: string | null
  is_approved: boolean
  created_at: string
}

export interface TimesheetPayload {
  engineer_id: number
  project_id: number
  assignment_id?: number | null
  work_date: string
  person_days: number
  description?: string | null
}

export interface ImportResult {
  created: number
  skipped: number
  errors: { row: number; message: string }[]
}

export const listTimesheets = (params?: {
  engineer_id?: number; project_id?: number; date_from?: string; date_to?: string
}) =>
  http.get<Timesheet[]>('/timesheets', { params }).then((r) => r.data)

export const createTimesheet = (p: TimesheetPayload) =>
  http.post<Timesheet>('/timesheets', p).then((r) => r.data)

export const updateTimesheet = (id: number, p: Partial<TimesheetPayload>) =>
  http.patch<Timesheet>(`/timesheets/${id}`, p).then((r) => r.data)

export const deleteTimesheet = (id: number) => http.delete(`/timesheets/${id}`)

export const approveTimesheet = (id: number) =>
  http.patch<Timesheet>(`/timesheets/${id}/approve`).then((r) => r.data)

export const downloadTemplateUrl = (): string => {
  // Direct download; auth header attached by interceptor via blob fetch instead
  return '/api/admin/timesheets/template'
}

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
  const { data } = await http.post<ImportResult>('/timesheets/import-excel', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
