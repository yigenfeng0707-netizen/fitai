import { View, Text, Image } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState, useCallback } from 'react'
import NavBar from '@/components/NavBar'
import { getMyBookings, cancelBooking, checkIn } from '@/services/booking'
import { formatDateTime, formatTime } from '@/utils/format'
import { BOOKING_STATUS_MAP, BOOKING_STATUS_COLOR } from '@/utils/constants'
import type { BookingInfo, BookingStatus } from '@/types'
import './index.scss'

type TabKey = 'upcoming' | 'past' | 'cancelled'

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'upcoming', label: '即将到来' },
  { key: 'past', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

export default function Booking() {
  const [activeTab, setActiveTab] = useState<TabKey>('upcoming')
  const [bookings, setBookings] = useState<BookingInfo[]>([])
  const [loading, setLoading] = useState(false)

  const loadBookings = useCallback(async () => {
    setLoading(true)
    try {
      const statusMap: Record<TabKey, string> = {
        upcoming: 'upcoming',
        past: 'completed',
        cancelled: 'cancelled',
      }
      const res = await getMyBookings({
        status: statusMap[activeTab],
        page: 1,
        pageSize: 50,
      })
      setBookings(res.items)
    } catch (error) {
      console.error('加载预约列表失败', error)
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useDidShow(() => {
    loadBookings()
  })

  const handleTabChange = (tab: TabKey) => {
    setActiveTab(tab)
  }

  const handleCancel = async (booking: BookingInfo) => {
    Taro.showModal({
      title: '确认取消',
      content: `确定要取消「${booking.courseName}」的预约吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await cancelBooking(booking.id)
            Taro.showToast({ title: '取消成功', icon: 'success' })
            loadBookings()
          } catch (error: any) {
            Taro.showToast({ title: error.message || '取消失败', icon: 'none' })
          }
        }
      },
    })
  }

  const handleCheckIn = async (booking: BookingInfo) => {
    try {
      await checkIn(booking.id)
      Taro.showToast({ title: '签到成功', icon: 'success' })
      loadBookings()
    } catch (error: any) {
      Taro.showToast({ title: error.message || '签到失败', icon: 'none' })
    }
  }

  return (
    <View className="page-booking">
      <NavBar title="我的预约" />

      {/* Tab 切换 */}
      <View className="booking-tabs">
        {tabs.map((tab) => (
          <View
            key={tab.key}
            className={`booking-tabs__item ${activeTab === tab.key ? 'booking-tabs__item--active' : ''}`}
            onClick={() => handleTabChange(tab.key)}
          >
            <Text className="booking-tabs__text">{tab.label}</Text>
          </View>
        ))}
      </View>

      {/* 预约列表 */}
      <View className="booking-list">
        {loading ? (
          <View className="booking-list__loading">
            <Text>加载中...</Text>
          </View>
        ) : bookings.length > 0 ? (
          bookings.map((booking) => (
            <View key={booking.id} className="booking-card">
              <Image
                className="booking-card__cover"
                src={booking.courseCover}
                mode="aspectFill"
              />
              <View className="booking-card__content">
                <View className="booking-card__header">
                  <Text className="booking-card__name">{booking.courseName}</Text>
                  <View
                    className="booking-card__status"
                    style={{ backgroundColor: `${BOOKING_STATUS_COLOR[booking.status]}15` }}
                  >
                    <Text
                      className="booking-card__status-text"
                      style={{ color: BOOKING_STATUS_COLOR[booking.status] }}
                    >
                      {BOOKING_STATUS_MAP[booking.status]}
                    </Text>
                  </View>
                </View>
                <View className="booking-card__info">
                  <Text className="booking-card__coach">{booking.coachName}</Text>
                  <Text className="booking-card__time">
                    {formatTime(booking.startTime)} - {formatTime(booking.endTime)}
                  </Text>
                  <Text className="booking-card__store">{booking.storeName}</Text>
                </View>
                {booking.status === 'upcoming' && (
                  <View className="booking-card__actions">
                    <View
                      className="booking-card__btn booking-card__btn--cancel"
                      onClick={() => handleCancel(booking)}
                    >
                      <Text>取消预约</Text>
                    </View>
                    <View
                      className="booking-card__btn booking-card__btn--checkin"
                      onClick={() => handleCheckIn(booking)}
                    >
                      <Text>签到</Text>
                    </View>
                  </View>
                )}
              </View>
            </View>
          ))
        ) : (
          <View className="booking-list__empty">
            <Text className="booking-list__empty-text">暂无预约记录</Text>
          </View>
        )}
      </View>
    </View>
  )
}
