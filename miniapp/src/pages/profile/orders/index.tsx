import { View, Text } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import NavBar from '@/components/NavBar'
import { useUser } from '@/store'
import { getOrderList } from '@/services/payment'
import { formatDate, formatMoney } from '@/utils/format'
import { ORDER_STATUS_MAP } from '@/utils/constants'
import type { OrderInfo } from '@/types'
import './index.scss'

export default function Orders() {
  const { state: userState } = useUser()
  const [orders, setOrders] = useState<OrderInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('all')

  useDidShow(() => {
    if (userState.isLoggedIn) {
      loadOrders()
    }
  })

  const loadOrders = async () => {
    setLoading(true)
    try {
      const data = await getOrderList()
      setOrders(data)
    } catch (error) {
      console.error('加载订单失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
  }

  const handlePay = (orderId: number) => {
    Taro.navigateTo({ url: `/pages/payment/index?orderId=${orderId}` })
  }

  return (
    <View className="page-orders">
      <NavBar title="订单记录" back />

      {/* 标签页 */}
      <View className="tabs">
        <View
          className={`tabs__item ${activeTab === 'all' ? 'tabs__item--active' : ''}`}
          onClick={() => handleTabChange('all')}
        >
          <Text>全部</Text>
        </View>
        <View
          className={`tabs__item ${activeTab === 'pending' ? 'tabs__item--active' : ''}`}
          onClick={() => handleTabChange('pending')}
        >
          <Text>待支付</Text>
        </View>
        <View
          className={`tabs__item ${activeTab === 'paid' ? 'tabs__item--active' : ''}`}
          onClick={() => handleTabChange('paid')}
        >
          <Text>已完成</Text>
        </View>
      </View>

      {/* 订单列表 */}
      {loading ? (
        <View className="loading">
          <Text>加载中...</Text>
        </View>
      ) : orders.length > 0 ? (
        <View className="order-list">
          {orders.map((order) => (
            <View key={order.id} className="order-card">
              <View className="order-card__header">
                <Text className="order-card__no">订单号: {order.orderNo}</Text>
                <View
                  className="order-card__status"
                  style={{
                    backgroundColor: order.paymentStatus === 'paid' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                  }}
                >
                  <Text
                    className="order-card__status-text"
                    style={{
                      color: order.paymentStatus === 'paid' ? '#10b981' : '#f59e0b',
                    }}
                  >
                    {ORDER_STATUS_MAP[order.paymentStatus] || order.paymentStatus}
                  </Text>
                </View>
              </View>
              <View className="order-card__body">
                <Text className="order-card__subject">{order.subject}</Text>
                <Text className="order-card__time">{formatDate(order.createdAt)}</Text>
              </View>
              <View className="order-card__footer">
                <Text className="order-card__amount">
                  ¥{formatMoney(order.actualAmount)}
                </Text>
                {order.paymentStatus === 'pending' && (
                  <View className="order-card__pay-btn" onClick={() => handlePay(order.id)}>
                    <Text className="order-card__pay-text">去支付</Text>
                  </View>
                )}
              </View>
            </View>
          ))}
        </View>
      ) : (
        <View className="empty">
          <Text className="empty__text">暂无订单记录</Text>
        </View>
      )}
    </View>
  )
}
