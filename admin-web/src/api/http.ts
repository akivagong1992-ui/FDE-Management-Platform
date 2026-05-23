import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api/admin', timeout: 15000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('mp_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(typeof msg === 'string' ? msg : '请求失败')
    if (err.response?.status === 401) {
      localStorage.removeItem('mp_token')
      if (location.pathname !== '/login') location.assign('/login')
    }
    return Promise.reject(err)
  },
)

export default http
