import client from './client'
import type { AnalyticsDashboard } from './types'

export const analyticsApi = {
  getDashboard: async (): Promise<AnalyticsDashboard> => {
    const response = await client.get('/api/v1/analytics/dashboard')
    return response.data
  },
}

export default analyticsApi
