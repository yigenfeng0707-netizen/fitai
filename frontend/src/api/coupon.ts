import client from './client'

export const couponApi = {
  create: async (data: any): Promise<any> => {
    const response = await client.post('/api/v1/coupons/', data)
    return response.data
  },

  getList: async (params?: { skip?: number; limit?: number }): Promise<any> => {
    const response = await client.get('/api/v1/coupons/', { params })
    return response.data
  },

  validate: async (code: string, amount: number): Promise<any> => {
    const response = await client.post('/api/v1/coupons/validate', { code, amount })
    return response.data
  },

  toggle: async (id: number): Promise<any> => {
    const response = await client.post(`/api/v1/coupons/${id}/toggle`)
    return response.data
  },

  delete: async (id: number): Promise<any> => {
    const response = await client.delete(`/api/v1/coupons/${id}`)
    return response.data
  },

  getUsages: async (couponId: number, params?: { skip?: number; limit?: number }): Promise<any> => {
    const response = await client.get(`/api/v1/coupons/${couponId}/usages`, { params })
    return response.data
  },
}

export default couponApi
