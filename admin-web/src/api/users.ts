import http from './http'

export interface User {
  id: number
  username: string
  full_name?: string | null
  email?: string | null
  role: string
  is_active: boolean
  engineer_id?: number | null
  vendor_id?: number | null
  created_at: string
}

export interface UserPayload {
  username: string
  password: string
  full_name?: string
  email?: string
  role: string
  is_active: boolean
  engineer_id?: number | null
  vendor_id?: number | null
}

export const listUsers = () => http.get<User[]>('/users').then((r) => r.data)
export const createUser = (p: UserPayload) => http.post<User>('/users', p).then((r) => r.data)
export const updateUser = (id: number, p: Partial<UserPayload>) =>
  http.patch<User>(`/users/${id}`, p).then((r) => r.data)
export const deleteUser = (id: number) => http.delete(`/users/${id}`)
