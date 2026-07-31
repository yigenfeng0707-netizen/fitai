import client from './client'
import type { AuditLog, ListResponse } from './types'

export const auditApi = {
  getList: async (params?: { skip?: number; limit?: number; user_id?: number; action?: string; resource?: string }): Promise<ListResponse<AuditLog>> => {
    const response = await client.get('/api/v1/audit-logs/', { params })
    return response.data
  },
}

export default auditApi
