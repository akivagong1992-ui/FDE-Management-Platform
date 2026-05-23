import http from './http'

export type VsfType = 'monthly_per_engineer' | 'project_milestone' | 'other'
export type VsfStatus = 'draft' | 'billed' | 'paid'

export interface VendorServiceFee {
  id: number
  vendor_id: number
  vendor_name?: string | null
  engineer_id?: number | null
  engineer_name?: string | null
  project_id?: number | null
  project_name?: string | null
  fee_type: VsfType
  period_start: string
  period_end: string
  amount: number | string
  currency: string
  invoice_no?: string | null
  description?: string | null
  status: VsfStatus
  paid_at?: string | null
  created_at: string
}

export interface VsfPayload {
  vendor_id: number
  engineer_id?: number | null
  project_id?: number | null
  fee_type?: VsfType
  period_start: string
  period_end: string
  amount: number
  invoice_no?: string | null
  description?: string | null
  status?: VsfStatus
}

export const listFees = (params?: { vendor_id?: number; engineer_id?: number; project_id?: number; status_filter?: VsfStatus }) =>
  http.get<VendorServiceFee[]>('/vendor-service-fees', { params }).then((r) => r.data)
export const createFee = (p: VsfPayload) =>
  http.post<VendorServiceFee>('/vendor-service-fees', p).then((r) => r.data)
export const updateFee = (id: number, p: Partial<VsfPayload>) =>
  http.patch<VendorServiceFee>(`/vendor-service-fees/${id}`, p).then((r) => r.data)
export const deleteFee = (id: number) => http.delete(`/vendor-service-fees/${id}`)
