import http from './http'

export interface Training {
  id: number
  engineer_id: number
  engineer_name?: string | null
  course_name: string
  provider?: string | null
  category?: string | null
  training_date: string
  hours: number | string
  cost?: number | string | null
  passed: boolean
  notes?: string | null
  created_at: string
}

export interface TrainingPayload {
  engineer_id: number
  course_name: string
  provider?: string | null
  category?: string | null
  training_date: string
  hours: number
  cost?: number | null
  passed?: boolean
  notes?: string | null
}

export const listTrainings = (engineer_id?: number) =>
  http.get<Training[]>('/trainings', { params: { engineer_id } }).then((r) => r.data)
export const createTraining = (p: TrainingPayload) =>
  http.post<Training>('/trainings', p).then((r) => r.data)
export const updateTraining = (id: number, p: Partial<TrainingPayload>) =>
  http.patch<Training>(`/trainings/${id}`, p).then((r) => r.data)
export const deleteTraining = (id: number) => http.delete(`/trainings/${id}`)
