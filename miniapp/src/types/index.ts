/** FitAI 小程序类型定义 */

/** 通用 API 响应 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/** 分页参数 */
export interface PaginationParams {
  page: number
  pageSize: number
}

/** 分页响应 */
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/** 用户信息 */
export interface UserInfo {
  id: number
  openId: string
  phone: string
  nickname: string
  avatar: string
  gender: number // 0-未知 1-男 2-女
  createdAt: string
}

/** 会员信息 */
export interface MemberInfo {
  id: number
  userId: number
  name: string
  phone: string
  avatar: string
  memberNo: string
  cardType: string
  cardBalance: number
  remainingCount: number
  expiryDate: string
  storeId: number
  storeName: string
  createdAt: string
}

/** 教练信息 */
export interface CoachInfo {
  id: number
  name: string
  avatar: string
  specialty: string
  introduction: string
  rating: number
}

/** 课程类型 */
export interface CourseType {
  id: number
  name: string
  icon: string
  color: string
  description: string
}

/** 课程信息 */
export interface CourseInfo {
  id: number
  name: string
  typeId: number
  typeName: string
  description: string
  cover: string
  duration: number // 分钟
  capacity: number
  calories: number
  level: 'beginner' | 'intermediate' | 'advanced'
}

/** 课程排期 */
export interface ScheduleInfo {
  id: number
  courseId: number
  courseName: string
  courseCover: string
  coachId: number
  coachName: string
  coachAvatar: string
  startTime: string
  endTime: string
  capacity: number
  bookedCount: number
  availableCount: number
  status: 'available' | 'full' | 'cancelled'
  storeId: number
  storeName: string
}

/** 预约状态 */
export type BookingStatus = 'upcoming' | 'completed' | 'cancelled' | 'checked_in'

/** 预约记录 */
export interface BookingInfo {
  id: number
  scheduleId: number
  courseId: number
  courseName: string
  courseCover: string
  coachName: string
  coachAvatar: string
  startTime: string
  endTime: string
  storeName: string
  status: BookingStatus
  checkedInAt?: string
  cancelledAt?: string
  createdAt: string
}

/** 签到记录 */
export interface CheckInRecord {
  id: number
  bookingId: number
  courseName: string
  checkInTime: string
  method: 'qr' | 'manual'
}

/** 会员卡信息 */
export interface CardInfo {
  id: number
  type: string
  name: string
  balance: number
  remainingCount: number
  totalCount: number
  expiryDate: string
  status: 'active' | 'expired' | 'frozen'
}

/** 体型测试记录 */
export interface BodyTestRecord {
  id: number
  weight: number
  bodyFat: number
  muscle: number
  bmi: number
  testDate: string
}

/** 支付订单 */
export interface OrderInfo {
  id: number
  orderNo: string
  amount: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  payMethod: string
  paidAt?: string
  createdAt: string
  description: string
}

/** 创建订单参数 */
export interface CreateOrderParams {
  cardTypeId: number
  payMethod: 'wechat'
}

/** 登录响应 */
export interface LoginResponse {
  token: string
  userInfo: UserInfo
  memberInfo?: MemberInfo
}

/** 用户状态 */
export interface UserState {
  token: string
  userInfo: UserInfo | null
  memberInfo: MemberInfo | null
  isLoggedIn: boolean
}

/** 用户 Action */
export type UserAction =
  | { type: 'LOGIN'; payload: LoginResponse }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_PROFILE'; payload: Partial<UserInfo> }
  | { type: 'UPDATE_MEMBER'; payload: MemberInfo }
  | { type: 'SET_TOKEN'; payload: string }

/** 应用全局状态 */
export interface AppState {
  loading: boolean
  currentStore: {
    id: number
    name: string
  } | null
}
