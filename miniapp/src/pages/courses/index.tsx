import { View, Text, ScrollView } from '@tarojs/components'
import { useState, useEffect, useMemo, useCallback } from 'react'
import dayjs from 'dayjs'
import NavBar from '@/components/NavBar'
import CourseCard from '@/components/CourseCard'
import { getScheduleList } from '@/services/course'
import type { ScheduleInfo } from '@/types'
import './index.scss'

/** 生成日期列表（前后7天） */
function generateDateList(): Array<{ date: string; label: string; weekday: string }> {
  const today = dayjs()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const list = []
  for (let i = -1; i < 7; i++) {
    const d = today.add(i, 'day')
    list.push({
      date: d.format('YYYY-MM-DD'),
      label: i === 0 ? '今天' : i === 1 ? '明天' : d.format('MM/DD'),
      weekday: `周${weekdays[d.day()]}`,
    })
  }
  return list
}

export default function Courses() {
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'))
  const [schedules, setSchedules] = useState<ScheduleInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [courseType, setCourseType] = useState<number | null>(null)

  const dateList = useMemo(() => generateDateList(), [])

  const loadSchedules = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = { date: selectedDate }
      if (courseType !== null) params.typeId = courseType
      const data = await getScheduleList(params)
      setSchedules(data)
    } catch (error) {
      console.error('加载课程失败', error)
    } finally {
      setLoading(false)
    }
  }, [selectedDate, courseType])

  useEffect(() => {
    loadSchedules()
  }, [loadSchedules])

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
  }

  return (
    <View className="page-courses">
      <NavBar title="课程" />

      {/* 日期选择器 */}
      <View className="date-picker">
        <ScrollView scrollX className="date-picker__scroll">
          {dateList.map((item) => (
            <View
              key={item.date}
              className={`date-picker__item ${item.date === selectedDate ? 'date-picker__item--active' : ''}`}
              onClick={() => handleDateSelect(item.date)}
            >
              <Text className="date-picker__label">{item.label}</Text>
              <Text className="date-picker__weekday">{item.weekday}</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* 课程类型筛选 */}
      <View className="filter-bar">
        <ScrollView scrollX className="filter-bar__scroll">
          <View
            className={`filter-bar__tag ${courseType === null ? 'filter-bar__tag--active' : ''}`}
            onClick={() => setCourseType(null)}
          >
            <Text>全部</Text>
          </View>
          <View
            className={`filter-bar__tag ${courseType === 1 ? 'filter-bar__tag--active' : ''}`}
            onClick={() => setCourseType(1)}
          >
            <Text>瑜伽</Text>
          </View>
          <View
            className={`filter-bar__tag ${courseType === 2 ? 'filter-bar__tag--active' : ''}`}
            onClick={() => setCourseType(2)}
          >
            <Text>健身</Text>
          </View>
          <View
            className={`filter-bar__tag ${courseType === 3 ? 'filter-bar__tag--active' : ''}`}
            onClick={() => setCourseType(3)}
          >
            <Text>舞蹈</Text>
          </View>
          <View
            className={`filter-bar__tag ${courseType === 4 ? 'filter-bar__tag--active' : ''}`}
            onClick={() => setCourseType(4)}
          >
            <Text>冥想</Text>
          </View>
        </ScrollView>
      </View>

      {/* 课程列表 */}
      <View className="course-list">
        {loading ? (
          <View className="course-list__loading">
            <Text>加载中...</Text>
          </View>
        ) : schedules.length > 0 ? (
          schedules.map((schedule) => (
            <CourseCard key={schedule.id} schedule={schedule} />
          ))
        ) : (
          <View className="course-list__empty">
            <Text className="course-list__empty-text">暂无课程安排</Text>
          </View>
        )}
      </View>
    </View>
  )
}
