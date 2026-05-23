import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '@/api/auth'

const parseNullableInt = (v: string | null): number | null => {
  if (v == null || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('mp_token'))
  const username = ref<string | null>(localStorage.getItem('mp_username'))
  const role = ref<string | null>(localStorage.getItem('mp_role'))
  const userId = ref<number | null>(parseNullableInt(localStorage.getItem('mp_user_id')))
  const engineerId = ref<number | null>(parseNullableInt(localStorage.getItem('mp_engineer_id')))

  async function login(u: string, p: string) {
    const resp = await authApi.login(u, p)
    token.value = resp.access_token
    username.value = resp.username
    role.value = resp.role
    userId.value = resp.user_id
    engineerId.value = resp.engineer_id ?? null
    localStorage.setItem('mp_token', resp.access_token)
    localStorage.setItem('mp_username', resp.username)
    localStorage.setItem('mp_role', resp.role)
    localStorage.setItem('mp_user_id', String(resp.user_id))
    if (resp.engineer_id != null) localStorage.setItem('mp_engineer_id', String(resp.engineer_id))
    else localStorage.removeItem('mp_engineer_id')
  }

  function logout() {
    token.value = null
    username.value = null
    role.value = null
    userId.value = null
    engineerId.value = null
    localStorage.removeItem('mp_token')
    localStorage.removeItem('mp_username')
    localStorage.removeItem('mp_role')
    localStorage.removeItem('mp_user_id')
    localStorage.removeItem('mp_engineer_id')
  }

  return { token, username, role, userId, engineerId, login, logout }
})
