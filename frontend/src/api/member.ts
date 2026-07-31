// 会员 API
import client from './client'
import type { Member, MemberCreate, MemberUpdate, ListResponse } from './types'

export const memberApi = {
  // 获取会员列表
  getList: async (params?: { skip?: number; limit?: number; search?: string }): Promise<ListResponse<Member>> => {
    const response = await client.get('/api/v1/members/', { params })
    return response.data
  },

  // 获取单个会员
  get: async (id: number): Promise<Member> => {
    const response = await client.get(`/api/v1/members/${id}`)
    return response.data
  },

  // 创建会员
  create: async (data: MemberCreate): Promise<Member> => {
    const response = await client.post('/api/v1/members/', data)
    return response.data
  },

  // 更新会员
  update: async (id: number, data: MemberUpdate): Promise<Member> => {
    const response = await client.put(`/api/v1/members/${id}`, data)
    return response.data
  },

  // 删除会员
  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/members/${id}`)
  },
}

export default memberApi
