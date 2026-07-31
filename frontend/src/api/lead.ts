import client from './client'
import type { Lead, LeadCreate, LeadUpdate, ListResponse } from './types'

export const leadApi = {
  getList: async (params?: { skip?: number; limit?: number; status?: string; source?: string; search?: string }): Promise<ListResponse<Lead>> => {
    const response = await client.get('/api/v1/leads/', { params })
    return response.data
  },

  get: async (id: number): Promise<Lead> => {
    const response = await client.get(`/api/v1/leads/${id}`)
    return response.data
  },

  create: async (data: LeadCreate): Promise<Lead> => {
    const response = await client.post('/api/v1/leads/', data)
    return response.data
  },

  update: async (id: number, data: LeadUpdate): Promise<Lead> => {
    const response = await client.put(`/api/v1/leads/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/leads/${id}`)
  },
}

export default leadApi
