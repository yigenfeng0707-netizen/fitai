import { View, Text, Swiper, SwiperItem, Image } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState, useEffect, useMemo } from 'react'
import dayjs from 'dayjs'
import NavBar from '@/components/NavBar'
import CourseCard from '@/components/CourseCard'
import { isLoggedIn } from '@/services/auth'
import { getScheduleList } from '@/services/course'
import { formatWeekday } from '@/utils/format'
import type { ScheduleInfo } from '@/types'
import './index.scss'

export default function Index() {
  const [todaySchedules, setTodaySchedules] = useState<ScheduleInfo[]>([])
  const [loading, setLoading] = useState(false)

  const today = useMemo(() => dayjs().format('YYYY-MM-DD'), [])
  const weekday = useMemo(() => formatWeekday(today), [today])
  const greeting = useMemo(() => {
    const hour = dayjs().hour()
    if (hour < 6) return '夜深了'
    if (hour < 12) return '早上好'
    if (hour < 14) return '中午好'
    if (hour < 18) return '下午好'
    return '晚上好'
  }, [])

  useDidShow(() => {
    if (isLoggedIn()) {
      loadTodaySchedules()
    }
  })

  const loadTodaySchedules = async () => {
    setLoading(true)
    try {
      const schedules = await getScheduleList({ date: today })
      setTodaySchedules(schedules.slice(0, 5))
    } catch (error) {
      console.error('加载今日课程失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBook = () => {
    Taro.switchTab({ url: '/pages/courses/index' })
  }

  const handleCheckIn = () => {
    Taro.navigateTo({ url: '/pages/checkin/index' })
  }

  const handleProfile = () => {
    Taro.switchTab({ url: '/pages/profile/index' })
  }

  return (
    <View className="page-index">
      <NavBar title="FitAI" transparent />

      {/* 欢迎横幅 */}
      <View className="banner">
        <Swiper
          className="banner__swiper"
          indicatorDots
          indicatorColor="rgba(255,255,255,0.4)"
          indicatorActiveColor="#ffffff"
          autoplay
          circular
          interval={5000}
        >
          <SwiperItem>
            <View className="banner__slide banner__slide--primary">
              <Text className="banner__greeting">{greeting}</Text>
              <Text className="banner__date">{today} {weekday}</Text>
              <Text className="banner__slogan">每一次练习，都是对自己的投资</Text>
            </View>
          </SwiperItem>
          <SwiperItem>
            <View className="banner__slide banner__slide--secondary">
              <Text className="banner__title">FitAI 智能健身</Text>
              <Text className="banner__desc">专业课程 / 科学训练 / 健康管理</Text>
            </View>
          </SwiperItem>
        </Swiper>
      </View>

      {/* 快捷操作 */}
      <View className="quick-actions">
        <View className="quick-actions__item" onClick={handleBook}>
          <View className="quick-actions__icon quick-actions__icon--book">
            <Text>&#xe60b;</Text>
          </View>
          <Text className="quick-actions__text">预约课程</Text>
        </View>
        <View className="quick-actions__item" onClick={handleCheckIn}>
          <View className="quick-actions__icon quick-actions__icon--checkin">
            <Text>&#xe60c;</Text>
          </View>
          <Text className="quick-actions__text">签到打卡</Text>
        </View>
        <View className="quick-actions__item" onClick={handleProfile}>
          <View className="quick-actions__icon quick-actions__icon--profile">
            <Text>&#xe60d;</Text>
          </View>
          <Text className="quick-actions__text">个人中心</Text>
        </View>
      </View>

      {/* 今日课程 */}
      <View className="section">
        <View className="section__header">
          <Text className="section__title">今日课程</Text>
          <Text className="section__more" onClick={handleBook}>
            查看全部 &gt;
          </Text>
        </View>
        {loading ? (
          <View className="section__loading">
            <Text>加载中...</Text>
          </View>
        ) : todaySchedules.length > 0 ? (
          todaySchedules.map((schedule) => (
            <CourseCard key={schedule.id} schedule={schedule} />
          ))
        ) : (
          <View className="section__empty">
            <Text className="section__empty-text">今天暂无课程安排</Text>
          </View>
        )}
      </View>

      {/* 门店信息 */}
      <View className="store-card">
        <View className="store-card__header">
          <Text className="store-card__title">FitAI 健身瑜伽工作室</Text>
        </View>
        <View className="store-card__info">
          <View className="store-card__row">
            <Text className="store-card__label">营业时间</Text>
            <Text className="store-card__value">周一至周日 07:00 - 22:00</Text>
          </View>
          <View className="store-card__row">
            <Text className="store-card__label">联系电话</Text>
            <Text className="store-card__value">400-888-8888</Text>
          </View>
          <View className="store-card__row">
            <Text className="store-card__label">门店地址</Text>
            <Text className="store-card__value">请查看详情</Text>
          </View>
        </View>
      </View>
    </View>
  )
}
