import client from './client'
import type { Order, OrderCreate, ListResponse } from './types'

export const orderApi = {
  getList: async (params?: { skip?: number; limit?: number; member_id?: number; payment_status?: string }): Promise<ListResponse<Order>> => {
    const response = await client.get('/api/v1/orders/', { params })
    return response.data
  },

  get: async (id: number): Promise<Order> => {
    const response = await client.get(`/api/v1/orders/${id}`)
    return response.data
  },

  create: async (data: OrderCreate): Promise<Order> => {
    const response = await client.post('/api/v1/orders/', data)
    return response.data
  },

  pay: async (id: number, payment_method: string = 'alipay'): Promise<{ success: boolean; message: string; data: { redirect_url?: string; trade_no?: string } }> => {
    const response = await client.post(`/api/v1/orders/${id}/pay?payment_method=${payment_method}`)
    return response.data
  },

  cancel: async (id: number, cancel_reason?: string): Promise<Order> => {
    const response = await client.post(`/api/v1/orders/${id}/cancel`, { cancel_reason })
    return response.data
  },

  refund: async (id: number, refund_amount?: number): Promise<Order> => {
    const response = await client.post(`/api/v1/orders/${id}/refund`, { refund_amount })
    return response.data
  },
}

export default orderApi
