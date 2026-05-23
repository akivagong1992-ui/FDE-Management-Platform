import http from './http'

export interface SalesPerson {
  id: number
  name: string
  employee_id?: string | null
  department?: string | null
  email?: string | null
  mobile?: string | null
  is_active: boolean
  notes?: string | null
  created_at: string
}

export type SalesPersonPayload = Omit<SalesPerson, 'id' | 'created_at'>

export const listSalesPersons = (activeOnly = false) =>
  http.get<SalesPerson[]>('/sales-persons', { params: { active_only: activeOnly } }).then((r) => r.data)
export const createSalesPerson = (p: Partial<SalesPersonPayload>) =>
  http.post<SalesPerson>('/sales-persons', p).then((r) => r.data)
export const updateSalesPerson = (id: number, p: Partial<SalesPersonPayload>) =>
  http.patch<SalesPerson>(`/sales-persons/${id}`, p).then((r) => r.data)
export const deleteSalesPerson = (id: number) => http.delete(`/sales-persons/${id}`)
