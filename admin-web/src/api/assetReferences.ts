import http from './http'

export interface AssetReference {
  id: number
  asset_id: number
  project_id: number
  project_name?: string | null
  estimated_hours_saved?: number | string | null
  notes?: string | null
  referenced_by_user_id?: number | null
  referenced_at: string
}

export interface ReferencePayload {
  project_id: number
  estimated_hours_saved?: number | null
  notes?: string | null
}

export const listReferences = (assetId: number) =>
  http.get<AssetReference[]>(`/knowledge-assets/${assetId}/references`).then((r) => r.data)
export const createReference = (assetId: number, payload: ReferencePayload) =>
  http.post<AssetReference>(`/knowledge-assets/${assetId}/references`, payload).then((r) => r.data)
export const deleteReference = (assetId: number, refId: number) =>
  http.delete(`/knowledge-assets/${assetId}/references/${refId}`)
