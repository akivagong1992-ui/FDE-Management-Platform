import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('mp_token'))
  const username = ref<string | null>(localStorage.getItem('mp_username'))
  const role = ref<string | null>(localStorage.getItem('mp_role'))

  async function login(u: string, p: string) {
    const resp = await authApi.login(u, p)
    token.value = resp.access_token
    username.value = resp.username
    role.value = resp.role
    localStorage.setItem('mp_token', resp.access_token)
    localStorage.setItem('mp_username', resp.username)
    localStorage.setItem('mp_role', resp.role)
  }

  function logout() {
    token.value = null
    username.value = null
    role.value = null
    localStorage.removeItem('mp_token')
    localStorage.removeItem('mp_username')
    localStorage.removeItem('mp_role')
  }

  return { token, username, role, login, logout }
})
