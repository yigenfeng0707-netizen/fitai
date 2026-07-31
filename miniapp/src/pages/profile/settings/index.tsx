import { View, Text, Switch } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState } from 'react'
import NavBar from '@/components/NavBar'
import { useUser } from '@/store'
import { logout } from '@/services/auth'
import './index.scss'

export default function Settings() {
  const { state: userState, dispatch } = useUser()
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)

  const handleLogout = async () => {
    const result = await Taro.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      confirmColor: '#7c5cfc',
    })

    if (result.confirm) {
      try {
        await logout()
        dispatch({ type: 'LOGOUT' })
        Taro.reLaunch({ url: '/pages/index/index' })
      } catch (error) {
        console.error('退出登录失败', error)
      }
    }
  }

  const handleAbout = () => {
    Taro.showModal({
      title: '关于 FitAI',
      content: 'FitAI 智能健身瑜伽管理系统 v1.0.0',
      showCancel: false,
      confirmColor: '#7c5cfc',
    })
  }

  return (
    <View className="page-settings">
      <NavBar title="设置" back />

      <View className="settings-group">
        <View className="settings-item">
          <Text className="settings-item__label">消息通知</Text>
          <Switch
            checked={notificationsEnabled}
            color="#7c5cfc"
            onChange={(e) => setNotificationsEnabled(e.detail.value)}
          />
        </View>
        <View className="settings-item" onClick={handleAbout}>
          <Text className="settings-item__label">关于 FitAI</Text>
          <Text className="settings-item__value">v1.0.0</Text>
        </View>
      </View>

      <View className="settings-group">
        <View className="settings-item settings-item--danger" onClick={handleLogout}>
          <Text className="settings-item__label settings-item__label--danger">退出登录</Text>
        </View>
      </View>
    </View>
  )
}
