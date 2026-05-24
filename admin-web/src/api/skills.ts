import http from './http'

export type SkillLevel = 'L1' | 'L2' | 'L3'

export interface Skill {
  id: number
  name: string             // 认证名称 e.g. CCIE 路由交换
  category: string         // 分类 e.g. 网络能力
  issuer?: string | null   // 厂商 e.g. Cisco
  level?: SkillLevel | null
  is_active: boolean
}

export type SkillPayload = Omit<Skill, 'id'>

export interface SkillBulkItem {
  issuer: string
  name: string
  level: SkillLevel
}

export interface SkillBulkImportPayload {
  category: string
  items: SkillBulkItem[]
}

export interface SkillBulkResult {
  created: number
  skipped: number
  skipped_names: string[]
}

export const listSkills = () => http.get<Skill[]>('/skills').then((r) => r.data)
export const createSkill = (p: Partial<SkillPayload>) =>
  http.post<Skill>('/skills', p).then((r) => r.data)
export const updateSkill = (id: number, p: Partial<SkillPayload>) =>
  http.patch<Skill>(`/skills/${id}`, p).then((r) => r.data)
export const deleteSkill = (id: number) => http.delete(`/skills/${id}`)
export const bulkImportSkills = (p: SkillBulkImportPayload) =>
  http.post<SkillBulkResult>('/skills/bulk-import', p).then((r) => r.data)
