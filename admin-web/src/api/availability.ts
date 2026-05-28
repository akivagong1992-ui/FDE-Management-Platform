import http from './http'

export interface AvailabilityDay {
  date: string  // YYYY-MM-DD
  busy: boolean
  assignments: { id: number; project_name: string }[]
}

export interface EngineerAvailability {
  id: number
  full_name: string
  vendor_id: number
  vendor_name?: string | null
  days: AvailabilityDay[]
  busy_day_count: number
  free_day_count: number
}

export interface AvailabilityResp {
  from: string
  to: string
  weeks: number
  engineers: EngineerAvailability[]
  generated_at: string
}

export const fetchAvailability = (params: {
  weeks?: number
  from?: string
  vendor_id?: number
} = {}) =>
  http.get<AvailabilityResp>('/availability/engineers', { params }).then((r) => r.data)
