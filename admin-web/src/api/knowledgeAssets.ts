import http from './http'

export type Confidentiality = 'public' | 'internal' | 'confidential'

export interface KnowledgeAsset {
  id: number
  project_id?: number | null
  project_name?: string | null
  category: string
  category_label?: string | null
  title: string
  summary?: string | null
  content?: string | null
  external_url?: string | null
  file_path?: string | null
  tags?: string | null
  confidentiality: Confidentiality
  created_by_user_id?: number | null
  created_at: string
  updated_at: string
}

export interface KnowledgeAssetPayload {
  project_id?: number | null
  category: string
  title: string
  summary?: string | null
  content?: string | null
  external_url?: string | null
  file_path?: string | null
  tags?: string | null
  confidentiality?: Confidentiality
}

export const listAssets = (params?: { category?: string; project_id?: number; keyword?: string }) =>
  http.get<KnowledgeAsset[]>('/knowledge-assets', { params }).then((r) => r.data)
export const getAsset = (id: number) =>
  http.get<KnowledgeAsset>(`/knowledge-assets/${id}`).then((r) => r.data)
export const createAsset = (p: KnowledgeAssetPayload) =>
  http.post<KnowledgeAsset>('/knowledge-assets', p).then((r) => r.data)
export const updateAsset = (id: number, p: Partial<KnowledgeAssetPayload>) =>
  http.patch<KnowledgeAsset>(`/knowledge-assets/${id}`, p).then((r) => r.data)
export const deleteAsset = (id: number) => http.delete(`/knowledge-assets/${id}`)
