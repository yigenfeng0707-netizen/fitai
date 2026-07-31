import { View, Text } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import NavBar from '@/components/NavBar'
import { useUser } from '@/store'
import { getBodyTestRecords } from '@/services/member'
import { formatDate } from '@/utils/format'
import type { BodyTestRecord } from '@/types'
import './index.scss'

export default function BodyTest() {
  const { state: userState } = useUser()
  const [records, setRecords] = useState<BodyTestRecord[]>([])
  const [loading, setLoading] = useState(false)

  useDidShow(() => {
    if (userState.isLoggedIn) {
      loadRecords()
    }
  })

  const loadRecords = async () => {
    setLoading(true)
    try {
      const data = await getBodyTestRecords()
      setRecords(data)
    } catch (error) {
      console.error('加载体测记录失败', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className="page-body-test">
      <NavBar title="体型测试记录" back />
      
      {loading ? (
        <View className="loading">
          <Text>加载中...</Text>
        </View>
      ) : records.length > 0 ? (
        <View className="record-list">
          {records.map((record) => (
            <View key={record.id} className="record-card">
              <View className="record-card__header">
                <Text className="record-card__date">{formatDate(record.testDate)}</Text>
                <Text className="record-card__type">{record.testType}</Text>
              </View>
              <View className="record-card__body">
                <View className="record-card__item">
                  <Text className="record-card__label">身高</Text>
                  <Text className="record-card__value">{record.height} cm</Text>
                </View>
                <View className="record-card__item">
                  <Text className="record-card__label">体重</Text>
                  <Text className="record-card__value">{record.weight} kg</Text>
                </View>
                <View className="record-card__item">
                  <Text className="record-card__label">体脂率</Text>
                  <Text className="record-card__value">{record.bodyFatRate}%</Text>
                </View>
                <View className="record-card__item">
                  <Text className="record-card__label">BMI</Text>
                  <Text className="record-card__value">{record.bmi}</Text>
                </View>
              </View>
              {record.remark && (
                <View className="record-card__footer">
                  <Text className="record-card__remark">{record.remark}</Text>
                </View>
              )}
            </View>
          ))}
        </View>
      ) : (
        <View className="empty">
          <Text className="empty__text">暂无体测记录</Text>
          <Text className="empty__desc">完成体测后记录将在此显示</Text>
        </View>
      )}
    </View>
  )
}
