import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useMemo } from 'react'
import './index.scss'

interface TabBarProps {
  current: number
  items: Array<{
    text: string
    icon: string
    activeIcon: string
    pagePath: string
  }>
}

export default function TabBar({ current, items }: TabBarProps) {
  const statusBarHeight = useMemo(() => {
    const sysInfo = Taro.getSystemInfoSync()
    return sysInfo.statusBarHeight || 20
  }, [])

  const handleSwitch = (index: number, pagePath: string) => {
    if (index === current) return
    Taro.switchTab({ url: `/${pagePath}` })
  }

  return (
    <View className="tabbar" style={{ paddingBottom: `${statusBarHeight}px` }}>
      {items.map((item, index) => (
        <View
          key={item.pagePath}
          className={`tabbar__item ${index === current ? 'tabbar__item--active' : ''}`}
          onClick={() => handleSwitch(index, item.pagePath)}
        >
          <Text className={`tabbar__icon ${index === current ? 'tabbar__icon--active' : ''}`}>
            {index === current ? item.activeIcon : item.icon}
          </Text>
          <Text className="tabbar__text">{item.text}</Text>
        </View>
      ))}
    </View>
  )
}
