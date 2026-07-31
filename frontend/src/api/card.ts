import client from './client'
import type { CardTransaction, ExpiringCard, CardRenewRequest, CardRechargeRequest, CardUpgradeRequest, ListResponse, Member } from './types'

export const cardApi = {
  renew: async (memberId: number, data: CardRenewRequest): Promise<CardTransaction> => {
    const response = await client.post(`/api/v1/cards/${memberId}/renew`, data)
    return response.data
  },

  recharge: async (memberId: number, data: CardRechargeRequest): Promise<CardTransaction> => {
    const response = await client.post(`/api/v1/cards/${memberId}/recharge`, data)
    return response.data
  },

  upgrade: async (memberId: number, data: CardUpgradeRequest): Promise<CardTransaction> => {
    const response = await client.post(`/api/v1/cards/${memberId}/upgrade`, data)
    return response.data
  },

  getTransactions: async (memberId: number, params?: { skip?: number; limit?: number; transaction_type?: string }): Promise<ListResponse<CardTransaction>> => {
    const response = await client.get(`/api/v1/cards/${memberId}/transactions`, { params })
    return response.data
  },

  getExpiring: async (days: number = 7): Promise<ExpiringCard[]> => {
    const response = await client.get('/api/v1/cards/expiring', { params: { days } })
    return response.data
  },

  getExpired: async (params?: { skip?: number; limit?: number }): Promise<ListResponse<Member>> => {
    const response = await client.get('/api/v1/cards/expired', { params })
    return response.data
  },
}

export default cardApi
