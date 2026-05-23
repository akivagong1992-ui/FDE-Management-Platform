import axios from 'axios'

const cockpitToken = (import.meta as any).env?.VITE_COCKPIT_TOKEN || 'cockpit-dev-token'

const http = axios.create({
  baseURL: '/api/cockpit',
  timeout: 15000,
  headers: { 'X-Cockpit-Token': cockpitToken },
})

export default http
