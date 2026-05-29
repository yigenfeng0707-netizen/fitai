import { get, post, del } from './request'
import type { BookingInfo, PaginatedData, PaginationParams } from '@/types'

/** 创建预约 */
export function createBooking(scheduleId: number): Promise<BookingInfo> {
  return post('/api/v1/bookings', { scheduleId }, { showLoading: true })
}

/** 取消预约 */
export function cancelBooking(bookingId: number): Promise<void> {
  return del(`/api/v1/bookings/${bookingId}`, undefined, { showLoading: true })
}

/** 获取我的预约列表 */
export function getMyBookings(params?: Partial<PaginationParams> & {
  status?: string
}): Promise<PaginatedData<BookingInfo>> {
  return get('/api/v1/bookings/mine', params)
}

/** 签到 */
export function checkIn(bookingId: number): Promise<void> {
  return post(`/api/v1/bookings/${bookingId}/check-in`, undefined, { showLoading: true })
}
