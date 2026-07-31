import client from './client'

export const subscriptionApi = {
  create: async (plan: string, amount?: number, auto_renew?: boolean): Promise<any> => {
    const response = await client.post('/api/v1/subscriptions/', null, {
      params: { plan, amount: amount ?? 0, auto_renew: auto_renew ?? false },
    })
    return response.data
  },

  getActive: async (): Promise<any> => {
    const response = await client.get('/api/v1/subscriptions/active')
    return response.data
  },

  getList: async (params?: { skip?: number; limit?: number }): Promise<any> => {
    const response = await client.get('/api/v1/subscriptions/', { params })
    return response.data
  },

  getPlans: async (): Promise<any> => {
    const response = await client.get('/api/v1/subscriptions/plans')
    return response.data
  },

  cancel: async (id: number): Promise<any> => {
    const response = await client.post(`/api/v1/subscriptions/${id}/cancel`)
    return response.data
  },

  renew: async (id: number, duration_months: number = 1, amount: number = 0): Promise<any> => {
    const response = await client.post(`/api/v1/subscriptions/${id}/renew`, null, {
      params: { duration_months, amount },
    })
    return response.data
  },

  upgrade: async (id: number, new_plan: string, duration_months: number = 0, amount: number = 0): Promise<any> => {
    const response = await client.post(`/api/v1/subscriptions/${id}/upgrade`, null, {
      params: { new_plan, duration_months, amount },
    })
    return response.data
  },

  toggleRenew: async (id: number): Promise<any> => {
    const response = await client.post(`/api/v1/subscriptions/${id}/toggle-renew`)
    return response.data
  },
}

export default subscriptionApi
