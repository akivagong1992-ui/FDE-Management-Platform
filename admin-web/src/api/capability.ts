import http from './http'

export interface SkillSnapshot {
  id: number
  engineer_id: number
  engineer_name?: string | null
  snapshot_date: string
  skill_count: number
  avg_level: number | string
  level?: number | null
  created_at: string
}

export interface SnapshotTriggerResult {
  snapshot_date: string
  created: number
  skipped: number
}

export interface TeamTrendPoint {
  snapshot_date: string
  engineer_count: number
  avg_skill_count: number
  avg_skill_level: number
}

export const listSnapshots = (engineer_id?: number) =>
  http.get<SkillSnapshot[]>('/skill-snapshots', { params: { engineer_id } }).then((r) => r.data)
export const triggerSnapshot = () =>
  http.post<SnapshotTriggerResult>('/skill-snapshots/trigger').then((r) => r.data)
export const teamTrend = () =>
  http.get<TeamTrendPoint[]>('/skill-snapshots/team-trend').then((r) => r.data)
