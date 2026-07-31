// 课程 API
import client from './client'
import type { Course, CourseCreate, CourseSchedule, ScheduleCreate, ListResponse } from './types'

export const courseApi = {
  // 获取课程列表
  getList: async (params?: { skip?: number; limit?: number }): Promise<ListResponse<Course>> => {
    const response = await client.get('/api/v1/courses/', { params })
    return response.data
  },

  // 获取单个课程
  get: async (id: number): Promise<Course> => {
    const response = await client.get(`/api/v1/courses/${id}`)
    return response.data
  },

  // 创建课程
  create: async (data: CourseCreate): Promise<Course> => {
    const response = await client.post('/api/v1/courses/', data)
    return response.data
  },

  // 更新课程
  update: async (id: number, data: Partial<CourseCreate>): Promise<Course> => {
    const response = await client.put(`/api/v1/courses/${id}`, data)
    return response.data
  },

  // 删除课程
  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/v1/courses/${id}`)
  },

  // 获取课程排期列表
  getSchedules: async (params?: { course_id?: number; skip?: number; limit?: number }): Promise<ListResponse<CourseSchedule>> => {
    const response = await client.get('/api/v1/courses/schedules/', { params })
    return response.data
  },

  // 创建课程排期
  createSchedule: async (data: ScheduleCreate): Promise<CourseSchedule> => {
    const response = await client.post('/api/v1/courses/schedules/', data)
    return response.data
  },
}

export default courseApi
