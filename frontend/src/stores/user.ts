import { defineStore } from 'pinia'
import request from '../api/request'

interface LoginResponse {
  message: string
  token: string
  user: {
    id: number
    username: string
    email: string
    phone: string
  }
}

interface UserInfo {
  id: number
  username: string
  email: string
  phone: string
}

export const useUserStore = defineStore(
  'user',
  {
    state: () => ({
      token:
        localStorage.getItem('token') || '',

      user: (() => {
        const value =
          localStorage.getItem('user')

        if (!value) {
          return null
        }

        try {
          return JSON.parse(value)
        } catch {
          return null
        }
      })() as UserInfo | null,
    }),

    getters: {
      isLoggedIn: (state) => {
        return !!state.token
      },
    },

    actions: {
      async login(username: string, password: string) {
        const response = await request.post<LoginResponse>(
          '/login',
          {
            username,
            password
          }
        )

        this.token = response.data.token

        localStorage.setItem(
          'token',
          response.data.token
        )

        this.user = response.data.user

        localStorage.setItem(
          'user',
          JSON.stringify(response.data.user)
        )

        return response.data
      },

      logout() {
        this.token = ''
        this.user = null

        localStorage.removeItem('token')
        localStorage.removeItem('user')
      },
    },
  }
)