import axios from 'axios'
import toast from 'react-hot-toast'

// Determine API URL: env var → Vercel (relative) → localhost fallback
const envUrl = import.meta.env.VITE_API_URL
const isVercel = window.location.hostname.includes('vercel.app')
const BASE_URL = envUrl || (isVercel ? '' : 'http://localhost:8000')

console.log('📡 API Configuration:', {
  envVar: envUrl,
  isVercel,
  finalUrl: BASE_URL || '(relative)',
  hostname: window.location.hostname,
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
})

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mb_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Global error handler
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err?.response?.data?.detail || err.message || 'Request failed'
    const url  = err?.config?.url || ''
    if (err?.response?.status === 401) {
      localStorage.removeItem('mb_token')
      localStorage.removeItem('mb_user')
      window.location.href = '/login'
    } else if (err?.response?.status !== 422 && !url.includes('/api/signatures')) {
      // suppress toasts for signature endpoints — handled gracefully in the page
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }).then(r => r.data),
  sendOtp: (email, purpose) =>
    api.post('/api/auth/send-otp', { email, purpose }).then(r => r.data),
  register: (email, full_name, password, otp) =>
    api.post('/api/auth/register', { email, full_name, password, otp }).then(r => r.data),
  resetPassword: (email, otp, new_password) =>
    api.post('/api/auth/reset-password', { email, otp, new_password }).then(r => r.data),
  me: () => api.get('/api/auth/me').then(r => r.data),
  oauthUrl: () => api.get('/api/auth/oauth/url').then(r => r.data),
  disconnect: () => api.delete('/api/auth/oauth/disconnect').then(r => r.data),
}

// ── Templates ─────────────────────────────────────────────────────────────────
export const templatesApi = {
  list: () => api.get('/api/templates/').then(r => r.data),
  create: (data) => api.post('/api/templates/', data).then(r => r.data),
  update: (id, data) => api.put(`/api/templates/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/api/templates/${id}`).then(r => r.data),
  listAttachments: () => api.get('/api/templates/attachments/').then(r => r.data),
  uploadAttachment: (file, isShared = false) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('is_shared', isShared.toString())
    return api.post('/api/templates/attachments/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data)
  },
  deleteAttachment: (id) => api.delete(`/api/templates/attachments/${id}`).then(r => r.data),
}

// ── Data ──────────────────────────────────────────────────────────────────────
export const dataApi = {
  parseExcel: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/api/data/parse-excel', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data)
  },
  sampleExcel: (variables) =>
    api.get('/api/data/sample-excel', {
      params: { variables },
      responseType: 'blob'
    }).then(r => r.data),
  generateDummy: (variable_names, count) =>
    api.post('/api/data/generate-dummy', { variable_names, count }).then(r => r.data),
}

// ── Campaigns ─────────────────────────────────────────────────────────────────
export const campaignsApi = {
  list: () => api.get('/api/campaigns/').then(r => r.data),
  create: (data) => api.post('/api/campaigns/', data).then(r => r.data),
  start: (id) => api.post(`/api/campaigns/${id}/send`).then(r => r.data),
  logs: (id) => api.get(`/api/campaigns/${id}/logs`).then(r => r.data),
  delete: (id) => api.delete(`/api/campaigns/${id}`).then(r => r.data),
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminApi = {
  stats: () => api.get('/api/admin/stats').then(r => r.data),
  users: () => api.get('/api/admin/users').then(r => r.data),
  toggleAdmin: (id) => api.put(`/api/admin/users/${id}/toggle-admin`).then(r => r.data),
  toggleActive: (id) => api.put(`/api/admin/users/${id}/toggle-active`).then(r => r.data),
  allCampaigns: () => api.get('/api/admin/campaigns').then(r => r.data),
  allSignatures: () => api.get('/api/signatures/admin/all').then(r => r.data),
}

// ── Admin user CRUD (added) ───────────────────────────────────────────────
export const adminUserApi = {
  create: (data) => api.post('/api/admin/users', data).then(r => r.data),
  update: (id, data) => api.put(`/api/admin/users/${id}`, data).then(r => r.data),
  delete: (id) => api.delete(`/api/admin/users/${id}`).then(r => r.data),
}

// ── Signature ──────────────────────────────────────────────────────────────────
export const signatureApi = {
  get:    ()     => api.get('/api/signatures/me').then(r => r.data),
  save:   (data) => api.post('/api/signatures/me', data).then(r => r.data),
  delete: ()     => api.delete('/api/signatures/me').then(r => r.data),
}
