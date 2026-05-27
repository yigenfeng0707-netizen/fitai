import client from './client'
import type { Subscription, ListResponse } from './types'

export const subscriptionApi = {
  create: async (plan: string, amount?: number, auto_renew?: boolean): Promise<Subscription> => {
    const response = await client.post('/api/v1/subscriptions/', { plan, amount, auto_renew })
    return response.data
  },

  getActive: async (): Promise<Subscription> => {
    const response = await client.get('/api/v1/subscriptions/active')
    return response.data
  },

  getList: async (params?: { skip?: number; limit?: number }): Promise<ListResponse<Subscription>> => {
    const response = await client.get('/api/v1/subscriptions/', { params })
    return response.data
  },
}

export default subscriptionApi
