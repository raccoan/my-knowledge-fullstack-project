import request from './request'

export interface LoginResponse {
  message: string
  token: string
}

export interface LoginParams {
  username: string
  password: string
}

export const login = async (
  data: LoginParams
): Promise<LoginResponse> => {

  const response = await request.post<LoginResponse>(
    '/login',
    data
  )

  return response.data
}