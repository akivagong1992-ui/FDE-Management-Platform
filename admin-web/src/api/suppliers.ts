import http from './http'

export interface Supplier {
  id: number
  name: string
  category?: string | null
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  payment_terms?: string | null
  is_active: boolean
  notes?: string | null
  created_at: string
}

export type SupplierPayload = Omit<Supplier, 'id' | 'created_at'>

export const listSuppliers = () => http.get<Supplier[]>('/suppliers').then((r) => r.data)
export const createSupplier = (p: Partial<SupplierPayload>) => http.post<Supplier>('/suppliers', p).then((r) => r.data)
export const updateSupplier = (id: number, p: Partial<SupplierPayload>) =>
  http.patch<Supplier>(`/suppliers/${id}`, p).then((r) => r.data)
export const deleteSupplier = (id: number) => http.delete(`/suppliers/${id}`)
