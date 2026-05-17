import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.code === 'ERR_NETWORK') {
      window.dispatchEvent(
        new CustomEvent('api:network-error', {
          detail: 'Sem conexão com o servidor',
        })
      )
    }

    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true })
        return api(originalRequest)
      } catch (refreshError) {
        // Evita loop de redirect quando o refresh falha na própria página de login
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export default api
