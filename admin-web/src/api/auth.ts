import http from './http'

export interface LoginResp {
  access_token: string
  token_type: string
  role: string
  username: string
  user_id: number
  engineer_id: number | null
}

export async function login(username: string, password: string): Promise<LoginResp> {
  const form = new URLSearchParams()
  form.append('username', username)
  form.append('password', password)
  const { data } = await http.post<LoginResp>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}
