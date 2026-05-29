import http from './http'

export interface EngineerSkillRow {
  id: number
  skill_id: number
  skill_name: string
  skill_category: string
  skill_issuer?: string | null
  skill_level?: string | null  // L1 / L2 / L3 — 来自 Skill 字典
  notes?: string | null
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
  status: string
  entry_date?: string | null
  exit_date?: string | null
  monthly_cost_to_telecom?: number | string | null
  notes?: string | null
  skills: EngineerSkillRow[]
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
  status?: string
  entry_date?: string | null
  exit_date?: string | null
  monthly_cost_to_telecom?: number | null
  notes?: string | null
  initial_skill_ids?: number[]  // 新增工程师时可附带技能字典 id
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
export const attachSkill = (engineerId: number, payload: { skill_id: number; notes?: string }) =>
  http.post<EngineerSkillRow>(`/engineers/${engineerId}/skills`, payload).then((r) => r.data)
export const detachSkill = (engineerId: number, esId: number) =>
  http.delete(`/engineers/${engineerId}/skills/${esId}`)
