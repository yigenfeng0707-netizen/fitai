import dayjs from 'dayjs'

/** 格式化日期时间 */
export function formatDateTime(dateStr: string, format = 'YYYY-MM-DD HH:mm'): string {
  if (!dateStr) return ''
  return dayjs(dateStr).format(format)
}

/** 格式化日期 */
export function formatDate(dateStr: string, format = 'YYYY-MM-DD'): string {
  if (!dateStr) return ''
  return dayjs(dateStr).format(format)
}

/** 格式化时间 */
export function formatTime(dateStr: string, format = 'HH:mm'): string {
  if (!dateStr) return ''
  return dayjs(dateStr).format(format)
}

/** 格式化日期为友好显示 */
export function formatDateFriendly(dateStr: string): string {
  const date = dayjs(dateStr)
  const today = dayjs()

  if (date.isSame(today, 'day')) return '今天'
  if (date.isSame(today.subtract(1, 'day'), 'day')) return '昨天'
  if (date.isSame(today.add(1, 'day'), 'day')) return '明天'

  return date.format('MM月DD日')
}

/** 格式化星期 */
export function formatWeekday(dateStr: string): string {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekdays[dayjs(dateStr).day()]
}

/** 格式化金额 */
export function formatMoney(amount: number): string {
  return (amount / 100).toFixed(2)
}

/** 格式化时长 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

/** 格式化卡路里 */
export function formatCalories(calories: number): string {
  return `${calories}kcal`
}

/** 获取相对时间 */
export function getRelativeTime(dateStr: string): string {
  const date = dayjs(dateStr)
  const now = dayjs()
  const diffMinutes = now.diff(date, 'minute')

  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  const diffHours = now.diff(date, 'hour')
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = now.diff(date, 'day')
  if (diffDays < 30) return `${diffDays}天前`
  return formatDate(dateStr)
}
