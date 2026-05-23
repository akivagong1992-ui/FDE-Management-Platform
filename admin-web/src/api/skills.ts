import http from './http'

export interface Skill {
  id: number
  name: string
  category: string
  description?: string | null
  is_active: boolean
}

export type SkillPayload = Omit<Skill, 'id'>

export const listSkills = () => http.get<Skill[]>('/skills').then((r) => r.data)
export const createSkill = (p: Partial<SkillPayload>) => http.post<Skill>('/skills', p).then((r) => r.data)
export const updateSkill = (id: number, p: Partial<SkillPayload>) =>
  http.patch<Skill>(`/skills/${id}`, p).then((r) => r.data)
export const deleteSkill = (id: number) => http.delete(`/skills/${id}`)
