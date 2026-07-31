// 认证 API
import client from './client'
import type { LoginRequest, LoginResponse, RegisterRequest, User } from './types'

export const authApi = {
  // 登录
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await client.post('/api/v1/auth/login', data)
    return response.data
  },

  // 注册
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await client.post('/api/v1/auth/register', data)
    return response.data
  },

  // 获取当前用户
  getCurrentUser: async (): Promise<User> => {
    const response = await client.get('/api/v1/auth/me')
    return response.data
  },
}

export default authApi
