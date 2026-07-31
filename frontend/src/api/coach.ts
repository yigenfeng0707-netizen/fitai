// 教练 API
import client from './client'
import type { Coach, CoachCreate, CoachUpdate, ListResponse } from './types'

export const coachApi = {
  // 获取教练列表
  getList: async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<ListResponse<Coach>> => {
    const response = await client.get('/api/v1/coaches/', { params })
    return response.data
  },

  // 获取单个教练
  get: async (id: number): Promise<Coach> => {
    const response = await client.get(`/api/v1/coaches/${id}`)
    return response.data
  },

  // 创建教练
  create: async (data: CoachCreate): Promise<Coach> => {
    const response = await client.post('/api/v1/coaches/', data)
    return response.data
  },

  // 更新教练
  update: async (id: number, data: CoachUpdate): Promise<Coach> => {
    const response = await client.put(`/api/v1/coaches/${id}`, data)
    return response.data
  },

  // 删除教练
  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/coaches/${id}`)
  },

  // 增加课时
  addHours: async (id: number, hours: number): Promise<Coach> => {
    const response = await client.post(`/api/v1/coaches/${id}/add-hours`, null, { params: { hours } })
    return response.data
  },
}

export default coachApi
