// API 类型定义
export interface User {
  id: number
  username: string
  email?: string
  role: 'super_admin' | 'store_owner' | 'coach' | 'receptionist'
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role?: string
}

// 会员
export interface Member {
  id: number
  name: string
  phone: string
  email?: string
  gender?: string
  birthday?: string
  card_type?: 'single' | 'monthly' | 'yearly'
  card_start_date?: string
  card_end_date?: string
  card_remaining_count: number
  card_balance: number
  level: number
  total_consumption: number
  status: 'active' | 'inactive' | 'expired'
  tags?: string[]
  notes?: string
  coach_id?: number
  created_at: string
  updated_at: string
}

export interface MemberCreate {
  name: string
  phone: string
  email?: string
  gender?: string
  birthday?: string
  coach_id?: number
  initial_card_type?: 'single' | 'monthly' | 'yearly'
  initial_card_count?: number
  initial_card_balance?: number
}

export interface MemberUpdate {
  name?: string
  phone?: string
  email?: string
  gender?: string
  birthday?: string
  card_type?: 'single' | 'monthly' | 'yearly'
  card_start_date?: string
  card_end_date?: string
  card_remaining_count?: number
  card_balance?: number
  level?: number
  status?: 'active' | 'inactive' | 'expired'
  tags?: string[]
  notes?: string
  coach_id?: number
}

// 教练
export interface Coach {
  id: number
  name: string
  phone: string
  email?: string
  specialization?: string
  introduction?: string
  is_active: boolean
  certificates?: string[]
  work_schedule?: Record<string, unknown>
  total_hours: number
  total_students: number
  avg_rating: number
  created_at: string
  updated_at: string
}

export interface CoachCreate {
  name: string
  phone: string
  email?: string
  specialization?: string
  introduction?: string
  certificates?: string[]
  work_schedule?: Record<string, unknown>
  is_active?: boolean
}

export interface CoachUpdate {
  name?: string
  phone?: string
  email?: string
  specialization?: string
  introduction?: string
  is_active?: boolean
}

// 课程
export interface Course {
  id: number
  name: string
  description?: string
  course_type: 'group' | 'private'
  duration_minutes: number
  room?: string
  price: number
  package_price?: number
  coach_id?: number
  is_active: boolean
  max_attendees: number
  created_at: string
  updated_at: string
}

export interface CourseCreate {
  name: string
  description?: string
  course_type: 'group' | 'private'
  duration_minutes: number
  room?: string
  price: number
  max_attendees?: number
}

export interface CourseSchedule {
  id: number
  course_id: number
  course_name: string
  course_type: string
  coach_id?: number
  start_time: string
  end_time: string
  status: 'scheduled' | 'completed' | 'cancelled'
  enrolled_count: number
  max_capacity: number
  room: string
  notes?: string
  created_at: string
}

export interface ScheduleCreate {
  course_id: number
  start_time: string
  end_time: string
  notes?: string
}

export interface ScheduleUpdate {
  start_time?: string
  end_time?: string
  status?: string
  notes?: string
}

// 预约
export interface Booking {
  id: number
  member_id: number
  schedule_id: number
  status: 'pending' | 'confirmed' | 'checked_in' | 'cancelled' | 'no_show'
  check_in_time?: string
  check_in_method?: string
  cancelled_at?: string
  cancelled_by?: number
  cancel_reason?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface BookingCreate {
  member_id: number
  schedule_id: number
  notes?: string
}

// 通用响应
export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
}

export interface ListResponse<T> {
  success: boolean
  message: string
  data: T[]
  total: number
  page: number
  page_size: number
}

// 订单
export interface Order {
  id: number
  order_no: string
  member_id: number
  amount: number
  discount: number
  actual_amount: number
  payment_method?: string
  payment_status: 'pending' | 'paid' | 'refunded' | 'cancelled'
  transaction_id?: string
  product_type?: string
  product_id?: number
  subject?: string
  operator_id?: number
  notes?: string
  cancel_reason?: string
  refund_amount: number
  refunded_at?: string
  created_at: string
  paid_at?: string
  expires_at?: string
}

export interface OrderCreate {
  member_id: number
  amount: number
  discount?: number
  actual_amount: number
  product_type?: string
  product_id?: number
  subject?: string
  notes?: string
}

// 订阅
export interface Subscription {
  id: number
  organization_id: number
  plan: string
  status: string
  start_date?: string
  end_date?: string
  auto_renew: boolean
  amount: number
  actual_amount: number
  order_id?: number
  created_at?: string
}

// AI - 体测记录
export interface BodyTestRecord {
  id: number
  member_id: number
  height?: number
  weight?: number
  body_fat_percentage?: number
  muscle_mass?: number
  bmi?: number
  bone_mass?: number
  body_water?: number
  visceral_fat?: number
  basal_metabolism?: number
  body_age?: number
  protein?: number
  score?: number
  notes?: string
  created_at: string
}

// AI - 体测分析
export interface BodyTestAnalysis {
  current: BodyTestRecord
  previous?: BodyTestRecord
  trends: Record<string, number>
  suggestions: string[]
}

// 潜客 CRM
export interface Lead {
  id: number
  name: string
  phone?: string
  gender?: string
  age?: number
  source: string
  status: string
  intent?: string
  expected_budget?: number
  notes?: string
  tags?: string[]
  follow_up_count: number
  last_contacted_at?: string
  assigned_to?: number
  converted_member_id?: number
  created_at: string
  updated_at: string
}

export interface LeadCreate {
  name: string
  phone?: string
  gender?: string
  age?: number
  source?: string
  status?: string
  intent?: string
  expected_budget?: number
  notes?: string
  tags?: string[]
  assigned_to?: number
}

export interface LeadUpdate {
  name?: string
  phone?: string
  gender?: string
  age?: number
  source?: string
  status?: string
  intent?: string
  expected_budget?: number
  notes?: string
  tags?: string[]
  assigned_to?: number
  converted_member_id?: number
}

// 经营分析
export interface AnalyticsRevenue {
  today: number
  week: number
  month: number
  prev_month: number
  month_growth: number
  trend: Array<{ date: string; revenue: number }>
}

export interface AnalyticsMembers {
  total: number
  active: number
  new_month: number
  trend: Array<{ date: string; count: number }>
}

export interface AnalyticsBookings {
  today: number
  checked_in_today: number
  week: number
  completion_rate: number
  hour_distribution: Array<{ hour: string; count: number }>
}

export interface AnalyticsCourses {
  top: Array<{ name: string; booking_count: number }>
}

export interface AnalyticsCoaches {
  week_load: Array<{ name: string; class_count: number }>
}

export interface AnalyticsDashboard {
  revenue: AnalyticsRevenue
  members: AnalyticsMembers
  bookings: AnalyticsBookings
  courses: AnalyticsCourses
  coaches: AnalyticsCoaches
}

// AI - 仪表盘洞察
export interface DashboardInsights {
  revenue_today: number
  revenue_month: number
  active_members: number
  new_members_month: number
  bookings_today: number
  class_completion_rate: number
  top_courses: Array<{ name: string; booking_count: number }>
  insights: string[]
}

// 会员卡交易
export interface CardTransaction {
  id: number
  member_id: number
  transaction_type: 'recharge' | 'renew' | 'upgrade' | 'consume' | 'refund' | 'freeze' | 'unfreeze'
  amount: number
  count_change: number
  balance_before: number
  balance_after: number
  count_before: number
  count_after: number
  card_type_before: string | null
  card_type_after: string | null
  description: string | null
  operator_id: number | null
  order_id: number | null
  created_at: string
}

export interface CardRenewRequest {
  card_type: 'single' | 'monthly' | 'quarterly' | 'yearly' | 'stored'
  duration_days: number
  amount?: number
  description?: string
}

export interface CardRechargeRequest {
  amount: number
  count?: number
  description?: string
}

export interface CardUpgradeRequest {
  new_card_type: 'single' | 'monthly' | 'quarterly' | 'yearly' | 'stored'
  amount?: number
  description?: string
}

export interface ExpiringCard {
  member_id: number
  member_name: string
  member_phone: string
  card_type: string | null
  card_end_date: string | null
  days_remaining: number
}

// 消息通知
export interface AppNotification {
  id: number
  user_id: number
  notification_type: 'system' | 'class_reminder' | 'card_expiring' | 'card_expired' | 'booking_confirm' | 'booking_cancel' | 'payment_success' | 'marketing'
  title: string
  content: string | null
  is_read: boolean
  link: string | null
  extra_data: unknown
  created_at: string
  read_at: string | null
}

export interface UnreadCountResponse {
  count: number
}

// 操作日志
export interface AuditLog {
  id: number
  user_id: number | null
  action: string
  resource: string | null
  resource_id: number | null
  detail: string | null
  old_value: unknown
  new_value: unknown
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

// 系统设置
export interface OrganizationInfo {
  id: number
  name: string
  slug: string
  plan: string
  status: string
  contact_name: string | null
  contact_phone: string | null
  contact_email: string | null
  settings: Record<string, unknown> | null
  is_active: boolean
  trial_ends_at: string | null
  created_at: string
}

export interface UserManageInfo {
  id: number
  username: string
  role: string
  is_active: boolean
  is_superuser: boolean
  last_login_at: string | null
  created_at: string
}

export interface RoleInfo {
  role: string
  permissions: string[]
}
