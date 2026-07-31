import client from './client'
import type { CourseSchedule, ScheduleCreate, ScheduleUpdate, ListResponse } from './types'

export const scheduleApi = {
  getList: async (params: {
    start_date?: string
    end_date?: string
    course_id?: number
    coach_id?: number
    skip?: number
    limit?: number
  }): Promise<ListResponse<CourseSchedule>> => {
    const response = await client.get('/api/v1/courses/schedules/', { params })
    return response.data
  },

  get: async (id: number): Promise<CourseSchedule> => {
    const response = await client.get(`/api/v1/courses/schedules/${id}`)
    return response.data
  },

  create: async (data: ScheduleCreate): Promise<CourseSchedule> => {
    const response = await client.post('/api/v1/courses/schedules/', data)
    return response.data
  },

  update: async (id: number, data: ScheduleUpdate): Promise<CourseSchedule> => {
    const response = await client.put(`/api/v1/courses/schedules/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/courses/schedules/${id}`)
  },

  batchCreate: async (schedules: ScheduleCreate[]): Promise<void> => {
    await client.post('/api/v1/courses/schedules/batch', { schedules })
  },
}

export default scheduleApi
