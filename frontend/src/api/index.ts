import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // token 过期，跳转到登录页
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API 方法
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (email: string, username: string, password: string) =>
    api.post('/auth/register', { email, username, password }),
  getMe: () => api.get('/auth/me'),
}

export const videoApi = {
  list: (params?: { skip?: number; limit?: number; status_filter?: string; search?: string }) =>
    api.get('/videos', { params }),
  get: (id: number) => api.get(`/videos/${id}`),
  scan: (directory?: string) => api.post('/videos/scan', { directory }),
  toggleFavorite: (id: number) => api.post(`/videos/${id}/favorite`),
  getSubtitle: (id: number) => api.get(`/videos/${id}/subtitle`),
  getSummary: (id: number) => api.get(`/videos/${id}/summary`),
}

export const searchApi = {
  search: async (q: string, limit?: number, search_type?: string) => {
    const result = await api.get('/search', { params: { q, limit, search_type } })
    return result.data
  },
  suggestions: async (q: string, limit?: number) => {
    const result = await api.get('/search/suggestions', { params: { q, limit } })
    return result.data
  },
}

export const noteApi = {
  list: (video_id?: number) => api.get('/notes', { params: { video_id } }),
  create: (data: { video_id: number; title?: string; content: string; timestamp?: number; tags?: string[] }) =>
    api.post('/notes', data),
  update: (id: number, data: any) => api.put(`/notes/${id}`, data),
  delete: (id: number) => api.delete(`/notes/${id}`),
}

export const settingsApi = {
  get: () => api.get('/settings'),
  save: (data: any) => api.post('/settings', data),
  testOllama: (data: any) => api.post('/settings/test-ollama', data),
}
