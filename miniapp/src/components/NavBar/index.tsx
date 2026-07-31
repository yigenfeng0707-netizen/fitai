import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useMemo } from 'react'
import './index.scss'

interface NavBarProps {
  title?: string
  showBack?: boolean
  transparent?: boolean
  customLeft?: React.ReactNode
  customRight?: React.ReactNode
}

export default function NavBar({
  title = '',
  showBack = false,
  transparent = false,
  customLeft,
  customRight,
}: NavBarProps) {
  const statusBarHeight = useMemo(() => {
    const sysInfo = Taro.getSystemInfoSync()
    return sysInfo.statusBarHeight || 20
  }, [])

  const navBarHeight = useMemo(() => {
    const menuInfo = Taro.getMenuButtonBoundingClientRect()
    return (menuInfo.top - statusBarHeight) * 2 + menuInfo.height
  }, [statusBarHeight])

  const contentStyle = useMemo(() => ({
    paddingTop: `${statusBarHeight}px`,
    height: `${navBarHeight}px`,
  }), [statusBarHeight, navBarHeight])

  return (
    <View className={`navbar ${transparent ? 'navbar--transparent' : ''}`}>
      <View className="navbar__content" style={contentStyle}>
        <View className="navbar__left">
          {customLeft || (showBack && (
            <View className="navbar__back" onClick={() => Taro.navigateBack()}>
              <Text className="navbar__back-icon">&#xe60a;</Text>
            </View>
          ))}
        </View>
        <View className="navbar__title">
          <Text className="navbar__title-text">{title}</Text>
        </View>
        <View className="navbar__right">
          {customRight}
        </View>
      </View>
    </View>
  )
}
