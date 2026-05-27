// 预约 API
import client from './client'
import type { Booking, BookingCreate, ListResponse } from './types'

export interface CheckinTodayData {
  total: number
  checked_in: number
  pending: number
  confirmed: number
  cancelled: number
  no_show: number
  schedules: CheckinScheduleGroup[]
}

export interface CheckinScheduleGroup {
  schedule_id: number
  course_name: string
  start_time: string
  end_time: string
  enrolled_count: number
  checked_in_count: number
  bookings: CheckinBookingItem[]
}

export interface CheckinBookingItem {
  id: number
  member_id: number
  member_name: string
  member_phone: string
  schedule_id: number
  course_name: string
  start_time: string
  end_time: string
  status: string
  check_in_time?: string
  check_in_method?: string
  notes?: string
}

export const bookingApi = {
  getList: async (params?: {
    skip?: number
    limit?: number
    member_id?: number
    schedule_id?: number
    status?: string
  }): Promise<ListResponse<Booking>> => {
    const response = await client.get('/api/v1/bookings/', { params })
    return response.data
  },

  getToday: async (): Promise<ListResponse<Booking>> => {
    const response = await client.get('/api/v1/bookings/today')
    return response.data
  },

  getCheckinToday: async (): Promise<CheckinTodayData> => {
    const response = await client.get('/api/v1/bookings/checkin/today')
    return response.data
  },

  get: async (id: number): Promise<Booking> => {
    const response = await client.get(`/api/v1/bookings/${id}`)
    return response.data
  },

  create: async (data: BookingCreate): Promise<Booking> => {
    const response = await client.post('/api/v1/bookings/', data)
    return response.data
  },

  checkIn: async (id: number, method = 'manual'): Promise<Booking> => {
    const response = await client.post(`/api/v1/bookings/${id}/checkin`, { check_in_method: method })
    return response.data
  },

  cancel: async (id: number, reason?: string): Promise<void> => {
    const response = await client.post(`/api/v1/bookings/${id}/cancel`, null, { params: { reason } })
    return response.data
  },
}

export default bookingApi
