import client from './client'
import type { AppNotification, UnreadCountResponse, ListResponse } from './types'

export interface NotificationBatchCreate {
  user_ids: number[]
  notification_type: string
  title: string
  content?: string
  link?: string
}

export const notificationApi = {
  getList: async (params?: { skip?: number; limit?: number; is_read?: boolean; notification_type?: string }): Promise<ListResponse<AppNotification>> => {
    const response = await client.get('/api/v1/notifications/', { params })
    return response.data
  },

  getUnreadCount: async (): Promise<UnreadCountResponse> => {
    const response = await client.get('/api/v1/notifications/unread-count')
    return response.data
  },

  markRead: async (id: number): Promise<AppNotification> => {
    const response = await client.put(`/api/v1/notifications/${id}/read`)
    return response.data
  },

  markAllRead: async (): Promise<{ success: boolean; message: string }> => {
    const response = await client.put('/api/v1/notifications/read-all')
    return response.data
  },

  delete: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await client.delete(`/api/v1/notifications/${id}`)
    return response.data
  },

  batchCreate: async (data: NotificationBatchCreate): Promise<{ success: boolean; message: string }> => {
    const response = await client.post('/api/v1/notifications/batch', data)
    return response.data
  },
}

export default notificationApi
