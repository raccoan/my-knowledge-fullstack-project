import axios from 'axios'

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
    console.log('Axios 请求失败:', error)
    console.log('请求地址:', error.config?.url)
    console.log('状态码:', error.response?.status)
    console.log('后端返回:', error.response?.data)

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