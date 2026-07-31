import { get } from './request'
import type { CourseInfo, ScheduleInfo, CoachInfo, PaginatedData, PaginationParams } from '@/types'

/** 获取课程列表 */
export function getCourseList(params?: Partial<PaginationParams> & {
  typeId?: number
  keyword?: string
}): Promise<PaginatedData<CourseInfo>> {
  return get('/api/v1/courses', params)
}

/** 获取课程详情 */
export function getCourseDetail(id: number): Promise<CourseInfo> {
  return get(`/api/v1/courses/${id}`)
}

/** 获取排期列表 */
export function getScheduleList(params: {
  date: string
  typeId?: number
  coachId?: number
}): Promise<ScheduleInfo[]> {
  return get('/api/v1/schedules', params)
}

/** 获取教练列表 */
export function getCoachList(): Promise<CoachInfo[]> {
  return get('/api/v1/coaches')
}
