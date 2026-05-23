import http from './http'

export interface NeedParty {
  id: number
  name: string
  party_type: string  // 见 CLIENT_TYPES（向后兼容老 internal_dept / external_company）
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  notes?: string | null
  show_in_cockpit: boolean
  logo_path?: string | null
  created_at: string
}

export type NeedPartyPayload = Omit<NeedParty, 'id' | 'created_at'>

export const listNeedParties = () => http.get<NeedParty[]>('/need-parties').then((r) => r.data)
export const createNeedParty = (p: Partial<NeedPartyPayload>) =>
  http.post<NeedParty>('/need-parties', p).then((r) => r.data)
export const updateNeedParty = (id: number, p: Partial<NeedPartyPayload>) =>
  http.patch<NeedParty>(`/need-parties/${id}`, p).then((r) => r.data)
export const deleteNeedParty = (id: number) => http.delete(`/need-parties/${id}`)

// 公共文件上传（logo / 证书附件复用同一端点）
// 注：不能手动设 Content-Type，让浏览器自动加 multipart boundary
export const uploadFile = async (file: File): Promise<{ saved_path: string }> => {
  const fd = new FormData()
  fd.append('file', file)
  const r = await http.post<{ saved_path: string }>('/files/upload', fd)
  return r.data
}

// 客户类型常用值（admin 下拉项 + driver 端展示）
export const CLIENT_TYPES = [
  '中资企业', '港资企业', '外资企业',
  '政府机构', '银行', '证券', '保险',
  '物流 / 航运', '公用事业', '互联网科技',
] as const
