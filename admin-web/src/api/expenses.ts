import http from './http'

export type ExpenseStatus = 'pending' | 'approved' | 'rejected' | 'paid'

export interface ExpenseRequest {
  id: number
  project_id: number
  project_name?: string | null
  supplier_id?: number | null
  supplier_name?: string | null
  expense_type: string
  expense_type_label?: string | null
  title: string
  amount: number | string
  currency: string
  expense_date?: string | null
  description?: string | null
  status: ExpenseStatus
  requested_by_user_id?: number | null
  approved_by_user_id?: number | null
  approved_at?: string | null
  approval_note?: string | null
  paid_at?: string | null
  created_at: string
  updated_at: string
}

export interface ExpensePayload {
  project_id: number
  supplier_id?: number | null
  expense_type: string
  title: string
  amount: number
  expense_date?: string | null
  description?: string | null
}

export const listExpenses = (params?: { project_id?: number; expense_type?: string; status_filter?: ExpenseStatus }) =>
  http.get<ExpenseRequest[]>('/expenses', { params }).then((r) => r.data)
export const createExpense = (p: ExpensePayload) =>
  http.post<ExpenseRequest>('/expenses', p).then((r) => r.data)
export const updateExpense = (id: number, p: Partial<ExpensePayload>) =>
  http.patch<ExpenseRequest>(`/expenses/${id}`, p).then((r) => r.data)
export const approveExpense = (id: number, note?: string) =>
  http.post<ExpenseRequest>(`/expenses/${id}/approve`, { approval_note: note || null }).then((r) => r.data)
export const rejectExpense = (id: number, note?: string) =>
  http.post<ExpenseRequest>(`/expenses/${id}/reject`, { approval_note: note || null }).then((r) => r.data)
export const markPaid = (id: number) =>
  http.post<ExpenseRequest>(`/expenses/${id}/mark-paid`).then((r) => r.data)
export const deleteExpense = (id: number) => http.delete(`/expenses/${id}`)
