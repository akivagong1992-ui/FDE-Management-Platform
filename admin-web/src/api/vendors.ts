import http from './http'

export interface Vendor {
  id: number
  name: string
  short_name?: string | null
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  payment_terms?: string | null
  cooperation_status: string
  notes?: string | null
  created_at: string
}

export type VendorPayload = Omit<Vendor, 'id' | 'created_at'>

export const listVendors = () => http.get<Vendor[]>('/vendors').then((r) => r.data)
export const createVendor = (p: Partial<VendorPayload>) => http.post<Vendor>('/vendors', p).then((r) => r.data)
export const updateVendor = (id: number, p: Partial<VendorPayload>) =>
  http.patch<Vendor>(`/vendors/${id}`, p).then((r) => r.data)
export const deleteVendor = (id: number) => http.delete(`/vendors/${id}`)
