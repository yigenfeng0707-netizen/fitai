import { View, Text, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { formatTime } from '@/utils/format'
import type { ScheduleInfo } from '@/types'
import './index.scss'

interface CourseCardProps {
  schedule: ScheduleInfo
  onClick?: (schedule: ScheduleInfo) => void
}

export default function CourseCard({ schedule, onClick }: CourseCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick(schedule)
    } else {
      Taro.navigateTo({
        url: `/pages/booking/index?scheduleId=${schedule.id}`,
      })
    }
  }

  return (
    <View className="course-card" onClick={handleClick}>
      <Image
        className="course-card__cover"
        src={schedule.courseCover}
        mode="aspectFill"
      />
      <View className="course-card__info">
        <Text className="course-card__name">{schedule.courseName}</Text>
        <View className="course-card__meta">
          <Text className="course-card__coach">{schedule.coachName}</Text>
          <Text className="course-card__time">
            {formatTime(schedule.startTime)} - {formatTime(schedule.endTime)}
          </Text>
        </View>
        <View className="course-card__footer">
          <View className="course-card__store">
            <Text className="course-card__store-text">{schedule.storeName}</Text>
          </View>
          <View className={`course-card__status ${schedule.availableCount > 0 ? 'available' : 'full'}`}>
            <Text className="course-card__status-text">
              {schedule.availableCount > 0
                ? `剩余 ${schedule.availableCount} 个名额`
                : '已满员'}
            </Text>
          </View>
        </View>
      </View>
    </View>
  )
}
