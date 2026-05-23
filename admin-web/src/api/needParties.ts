import http from './http'

export interface NeedParty {
  id: number
  name: string
  party_type: 'internal_dept' | 'external_company'
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  notes?: string | null
  created_at: string
}

export type NeedPartyPayload = Omit<NeedParty, 'id' | 'created_at'>

export const listNeedParties = () => http.get<NeedParty[]>('/need-parties').then((r) => r.data)
export const createNeedParty = (p: Partial<NeedPartyPayload>) =>
  http.post<NeedParty>('/need-parties', p).then((r) => r.data)
export const updateNeedParty = (id: number, p: Partial<NeedPartyPayload>) =>
  http.patch<NeedParty>(`/need-parties/${id}`, p).then((r) => r.data)
export const deleteNeedParty = (id: number) => http.delete(`/need-parties/${id}`)
