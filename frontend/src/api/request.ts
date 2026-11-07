import axios from 'axios'
import { parseApiError } from './errors'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

request.interceptors.response.use(
  (response) => {
    return response
  },

  (error) => {
    // 仅转换准入类错误，保持其余接口原有的 AxiosError 契约；不输出带 Token 的请求对象。
    if (error.response?.status === 429 || error.response?.status === 503) {
      return Promise.reject(parseApiError(
        error.response.status,
        error.response.data,
        error.response.headers?.['retry-after'],
      ))
    }

    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes('/login')
    ) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }

    return Promise.reject(error)
  }
)

export default request
