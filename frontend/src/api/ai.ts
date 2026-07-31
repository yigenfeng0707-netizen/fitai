import client from './client'
import type { BodyTestRecord, BodyTestAnalysis, DashboardInsights } from './types'

export const aiApi = {
  createBodyTest: async (memberId: number, data: Partial<BodyTestRecord>): Promise<BodyTestRecord> => {
    const response = await client.post(`/api/v1/ai/members/${memberId}/body-tests`, data)
    return response.data
  },

  getBodyTests: async (memberId: number, params?: { skip?: number; limit?: number }): Promise<{ data: BodyTestRecord[]; total: number }> => {
    const response = await client.get(`/api/v1/ai/members/${memberId}/body-tests`, { params })
    return response.data
  },

  analyzeBodyTest: async (memberId: number): Promise<BodyTestAnalysis> => {
    const response = await client.get(`/api/v1/ai/members/${memberId}/body-tests/latest`)
    return response.data
  },

  recommendCourses: async (memberId: number): Promise<Array<{ course_id: number; course_name: string; score: number; reason: string }>> => {
    const response = await client.get(`/api/v1/ai/members/${memberId}/recommendations`)
    return response.data
  },

  getInsights: async (): Promise<DashboardInsights> => {
    const response = await client.get('/api/v1/ai/dashboard/insights')
    return response.data
  },
}

export default aiApi
