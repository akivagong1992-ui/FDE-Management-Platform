import http from './http'

export interface EngineerSkillRow {
  id: number
  skill_id: number
  skill_name: string
  skill_category: string
  level: number
  notes?: string | null
}

export interface Certificate {
  id: number
  name: string
  issuer?: string | null
  cert_number?: string | null
  issue_date?: string | null
  expiry_date?: string | null
  file_path?: string | null
}

export interface Engineer {
  id: number
  vendor_id: number
  vendor_name?: string | null
  employment_form: 'vendor_direct' | 'vendor_via_labor'
  labor_company?: string | null
  full_name: string
  english_name?: string | null
  gender?: string | null
  birth_date?: string | null
  mobile?: string | null
  email?: string | null
  id_doc_type?: 'HKID' | 'passport' | 'mainland_id' | null
  id_doc_number_masked: string
  level?: number | null
  status: string
  entry_date?: string | null
  exit_date?: string | null
  monthly_cost_to_telecom?: number | string | null
  monthly_real_cost?: number | string | null
  notes?: string | null
  skills: EngineerSkillRow[]
  certificates: Certificate[]
  created_at: string
}

export interface EngineerPayload {
  vendor_id: number
  employment_form: 'vendor_direct' | 'vendor_via_labor'
  labor_company?: string | null
  full_name: string
  english_name?: string | null
  gender?: string | null
  birth_date?: string | null
  mobile?: string | null
  email?: string | null
  id_doc_type?: string | null
  id_doc_number?: string | null
  level?: number | null
  status?: string
  entry_date?: string | null
  exit_date?: string | null
  monthly_cost_to_telecom?: number | null
  monthly_real_cost?: number | null
  notes?: string | null
}

export const listEngineers = (params?: { vendor_id?: number; status_filter?: string }) =>
  http.get<Engineer[]>('/engineers', { params }).then((r) => r.data)
export const getEngineer = (id: number) => http.get<Engineer>(`/engineers/${id}`).then((r) => r.data)
export const createEngineer = (p: EngineerPayload) =>
  http.post<Engineer>('/engineers', p).then((r) => r.data)
export const updateEngineer = (id: number, p: Partial<EngineerPayload>) =>
  http.patch<Engineer>(`/engineers/${id}`, p).then((r) => r.data)
export const deleteEngineer = (id: number) => http.delete(`/engineers/${id}`)
export const revealEngineerId = (id: number) =>
  http.get<{ id: number; id_doc_type: string; id_doc_number: string }>(`/engineers/${id}/sensitive`).then((r) => r.data)
export const attachSkill = (engineerId: number, payload: { skill_id: number; level: number; notes?: string }) =>
  http.post<EngineerSkillRow>(`/engineers/${engineerId}/skills`, payload).then((r) => r.data)
export const detachSkill = (engineerId: number, esId: number) =>
  http.delete(`/engineers/${engineerId}/skills/${esId}`)
export const addCertificate = (engineerId: number, payload: Partial<Certificate>) =>
  http.post<Certificate>(`/engineers/${engineerId}/certificates`, payload).then((r) => r.data)
export const deleteCertificate = (engineerId: number, certId: number) =>
  http.delete(`/engineers/${engineerId}/certificates/${certId}`)
