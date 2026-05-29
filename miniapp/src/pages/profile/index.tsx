import { View, Text, Image } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import NavBar from '@/components/NavBar'
import { useUser } from '@/store'
import { getProfile, getCardInfo } from '@/services/member'
import { formatDate } from '@/utils/format'
import { CARD_STATUS_MAP } from '@/utils/constants'
import type { MemberInfo, CardInfo } from '@/types'
import './index.scss'

export default function Profile() {
  const { state: userState } = useUser()
  const [memberInfo, setMemberInfo] = useState<MemberInfo | null>(null)
  const [cardInfo, setCardInfo] = useState<CardInfo | null>(null)

  useDidShow(() => {
    if (userState.isLoggedIn) {
      loadProfile()
    }
  })

  const loadProfile = async () => {
    try {
      const [profile, card] = await Promise.all([
        getProfile(),
        getCardInfo(),
      ])
      setMemberInfo(profile)
      setCardInfo(card)
    } catch (error) {
      console.error('加载个人资料失败', error)
    }
  }

  const handleLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const handleBodyTest = () => {
    Taro.navigateTo({ url: '/pages/profile/body-test' })
  }

  const handleOrders = () => {
    Taro.navigateTo({ url: '/pages/profile/orders' })
  }

  const handleSettings = () => {
    Taro.navigateTo({ url: '/pages/profile/settings' })
  }

  // 未登录状态
  if (!userState.isLoggedIn) {
    return (
      <View className="page-profile">
        <NavBar title="我的" />
        <View className="profile-login" onClick={handleLogin}>
          <View className="profile-login__avatar">
            <Text className="profile-login__avatar-text">?</Text>
          </View>
          <Text className="profile-login__text">点击登录</Text>
          <Text className="profile-login__desc">登录后查看会员信息</Text>
        </View>
      </View>
    )
  }

  return (
    <View className="page-profile">
      <NavBar title="我的" />

      {/* 用户信息卡片 */}
      <View className="profile-header">
        <Image
          className="profile-header__avatar"
          src={memberInfo?.avatar || userState.userInfo?.avatar || ''}
          mode="aspectFill"
        />
        <View className="profile-header__info">
          <Text className="profile-header__name">
            {memberInfo?.name || userState.userInfo?.nickname || '会员'}
          </Text>
          <Text className="profile-header__member-no">
            会员号: {memberInfo?.memberNo || '--'}
          </Text>
        </View>
      </View>

      {/* 会员卡信息 */}
      {cardInfo && (
        <View className="card-info">
          <View className="card-info__header">
            <Text className="card-info__title">{cardInfo.name}</Text>
            <View
              className="card-info__status"
              style={{
                backgroundColor: cardInfo.status === 'active' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(156, 163, 175, 0.1)',
              }}
            >
              <Text
                className="card-info__status-text"
                style={{
                  color: cardInfo.status === 'active' ? '#10b981' : '#9ca3af',
                }}
              >
                {CARD_STATUS_MAP[cardInfo.status]}
              </Text>
            </View>
          </View>
          <View className="card-info__stats">
            <View className="card-info__stat">
              <Text className="card-info__stat-value">{cardInfo.remainingCount}</Text>
              <Text className="card-info__stat-label">剩余次数</Text>
            </View>
            <View className="card-info__divider" />
            <View className="card-info__stat">
              <Text className="card-info__stat-value">{cardInfo.totalCount}</Text>
              <Text className="card-info__stat-label">总次数</Text>
            </View>
            <View className="card-info__divider" />
            <View className="card-info__stat">
              <Text className="card-info__stat-value">{formatDate(cardInfo.expiryDate)}</Text>
              <Text className="card-info__stat-label">有效期至</Text>
            </View>
          </View>
        </View>
      )}

      {/* 功能菜单 */}
      <View className="profile-menu">
        <View className="profile-menu__item" onClick={handleBodyTest}>
          <Text className="profile-menu__icon">&#xe60e;</Text>
          <Text className="profile-menu__text">体型测试记录</Text>
          <Text className="profile-menu__arrow">&gt;</Text>
        </View>
        <View className="profile-menu__item" onClick={handleOrders}>
          <Text className="profile-menu__icon">&#xe60f;</Text>
          <Text className="profile-menu__text">订单记录</Text>
          <Text className="profile-menu__arrow">&gt;</Text>
        </View>
        <View className="profile-menu__item" onClick={handleSettings}>
          <Text className="profile-menu__icon">&#xe610;</Text>
          <Text className="profile-menu__text">设置</Text>
          <Text className="profile-menu__arrow">&gt;</Text>
        </View>
      </View>
    </View>
  )
}
