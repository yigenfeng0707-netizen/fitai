import { View, Text, Image } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import NavBar from '@/components/NavBar'
import { useUser } from '@/store'
import { getMyBookings, checkIn } from '@/services/booking'
import { getCheckinQRCode } from '@/services/member'
import { formatTime } from '@/utils/format'
import type { BookingInfo } from '@/types'
import './index.scss'

export default function CheckIn() {
  const { state: userState } = useUser()
  const [todayBookings, setTodayBookings] = useState<BookingInfo[]>([])
  const [checkedInIds, setCheckedInIds] = useState<Set<number>>(new Set())
  const [qrCodeUrl, setQrCodeUrl] = useState('')
  const [qrToken, setQrToken] = useState('')
  const [qrExpires, setQrExpires] = useState(0)

  useDidShow(() => {
    if (userState.isLoggedIn) {
      loadTodayBookings()
      loadQRCode()
    }
  })

  const loadTodayBookings = async () => {
    try {
      const res = await getMyBookings({
        status: 'upcoming',
        page: 1,
        pageSize: 50,
      })
      setTodayBookings(res.items)
    } catch (error) {
      console.error('加载今日预约失败', error)
    }
  }

  const loadQRCode = async () => {
    try {
      const data = await getCheckinQRCode()
      setQrCodeUrl(data.qrcode)
      setQrToken(data.token)
      setQrExpires(data.expires_in)
    } catch (error) {
      console.error('加载签到码失败', error)
    }
  }

  const handleCheckIn = async (booking: BookingInfo) => {
    try {
      await checkIn(booking.id)
      setCheckedInIds((prev) => new Set(prev).add(booking.id))
      Taro.showToast({ title: '签到成功', icon: 'success' })
    } catch (error: any) {
      Taro.showToast({ title: error.message || '签到失败', icon: 'none' })
    }
  }

  const isCheckedIn = (bookingId: number) => checkedInIds.has(bookingId)

  return (
    <View className="page-checkin">
      <NavBar title="签到" />

      {/* 签到码区域 */}
      <View className="checkin-qr">
        <View className="checkin-qr__box">
          {qrCodeUrl ? (
            <Image
              className="checkin-qr__image"
              src={qrCodeUrl}
              mode="aspectFit"
            />
          ) : (
            <View className="checkin-qr__placeholder">
              <Text className="checkin-qr__placeholder-text">加载中...</Text>
            </View>
          )}
        </View>
        <Text className="checkin-qr__tip">请将二维码展示给前台工作人员扫描</Text>
        {qrExpires > 0 && (
          <Text className="checkin-qr__expires">二维码 {Math.floor(qrExpires / 60)} 分钟内有效</Text>
        )}
      </View>

      {/* 手动签到 */}
      <View className="checkin-manual">
        <View
          className="checkin-manual__btn"
          onClick={() => {
            if (todayBookings.length > 0) {
              handleCheckIn(todayBookings[0])
            } else {
              Taro.showToast({ title: '今日暂无预约', icon: 'none' })
            }
          }}
        >
          <Text className="checkin-manual__btn-text">手动签到</Text>
        </View>
      </View>

      {/* 今日签到状态 */}
      <View className="checkin-status">
        <Text className="checkin-status__title">今日签到状态</Text>
        {todayBookings.length > 0 ? (
          todayBookings.map((booking) => (
            <View key={booking.id} className="checkin-status__item">
              <View className="checkin-status__info">
                <Text className="checkin-status__course">{booking.courseName}</Text>
                <Text className="checkin-status__time">
                  {formatTime(booking.startTime)} - {formatTime(booking.endTime)}
                </Text>
              </View>
              <View
                className={`checkin-status__badge ${
                  isCheckedIn(booking.id) ? 'checkin-status__badge--done' : 'checkin-status__badge--pending'
                }`}
              >
                <Text className="checkin-status__badge-text">
                  {isCheckedIn(booking.id) ? '已签到' : '未签到'}
                </Text>
              </View>
            </View>
          ))
        ) : (
          <View className="checkin-status__empty">
            <Text className="checkin-status__empty-text">今日暂无预约课程</Text>
          </View>
        )}
      </View>
    </View>
  )
}
