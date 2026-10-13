import axios from 'axios'
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api' })
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use(r => r, async error => {
  const original = error.config
  if (error.response?.status === 401 && !original?._retried && localStorage.getItem('refresh') && !String(original?.url).includes('/auth/token')) {
    original._retried = true
    try {
      const response = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, { refresh: localStorage.getItem('refresh') })
      localStorage.setItem('access', response.data.access)
      original.headers.Authorization = `Bearer ${response.data.access}`
      return api(original)
    } catch { localStorage.removeItem('access'); localStorage.removeItem('refresh') }
  }
  return Promise.reject(error)
})
