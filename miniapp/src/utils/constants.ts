/** API 基础地址 */
export const BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://api.fitai.com'
  : 'https://dev-api.fitai.com'

/** 请求超时时间 (ms) */
export const REQUEST_TIMEOUT = 15000

/** 分页默认值 */
export const DEFAULT_PAGE = 1
export const DEFAULT_PAGE_SIZE = 20

/** 课程等级 */
export const COURSE_LEVELS = {
  beginner: '初级',
  intermediate: '中级',
  advanced: '高级',
} as const

/** 预约状态映射 */
export const BOOKING_STATUS_MAP = {
  upcoming: '待上课',
  completed: '已完成',
  cancelled: '已取消',
  checked_in: '已签到',
} as const

/** 预约状态颜色 */
export const BOOKING_STATUS_COLOR = {
  upcoming: '#7c5cfc',
  completed: '#10b981',
  cancelled: '#9ca3af',
  checked_in: '#10b981',
} as const

/** 会员卡状态 */
export const CARD_STATUS_MAP = {
  active: '有效',
  expired: '已过期',
  frozen: '已冻结',
} as const

/** 订单状态 */
export const ORDER_STATUS_MAP = {
  pending: '待支付',
  paid: '已支付',
  cancelled: '已取消',
  refunded: '已退款',
} as const
