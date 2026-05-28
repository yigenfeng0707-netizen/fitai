import client from './client'
import type { ListResponse } from './types'

export interface Campaign {
  id: number
  organization_id: number
  name: string
  description: string | null
  campaign_type: string
  status: string
  channels: string[] | null
  target_audience: Record<string, unknown> | null
  target_count: number
  budget: number
  actual_cost: number
  start_date: string | null
  end_date: string | null
  sent_count: number
  opened_count: number
  converted_count: number
  converted_revenue: number
  created_at: string
  updated_at: string
}

export interface CampaignCreate {
  name: string
  description?: string
  campaign_type?: string
  channels?: string[]
  target_audience?: Record<string, unknown>
  target_count?: number
  budget?: number
  start_date?: string
  end_date?: string
}

export interface CampaignUpdate {
  name?: string
  description?: string
  status?: string
  channels?: string[]
  target_audience?: Record<string, unknown>
  target_count?: number
  budget?: number
  actual_cost?: number
  start_date?: string
  end_date?: string
  sent_count?: number
  opened_count?: number
  converted_count?: number
  converted_revenue?: number
}

export const campaignApi = {
  getList: async (params?: { skip?: number; limit?: number; status?: string }): Promise<ListResponse<Campaign>> => {
    const response = await client.get('/api/v1/campaigns/', { params })
    return response.data
  },

  get: async (id: number): Promise<Campaign> => {
    const response = await client.get(`/api/v1/campaigns/${id}`)
    return response.data
  },

  create: async (data: CampaignCreate): Promise<Campaign> => {
    const response = await client.post('/api/v1/campaigns/', data)
    return response.data
  },

  update: async (id: number, data: CampaignUpdate): Promise<Campaign> => {
    const response = await client.put(`/api/v1/campaigns/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/campaigns/${id}`)
  },
}
