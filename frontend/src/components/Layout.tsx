import { useEffect, useState } from 'react'
import { Layout as AntLayout, Menu, Avatar, Dropdown, Badge } from 'antd'
import {
  HomeOutlined,
  TeamOutlined,
  CalendarOutlined,
  ScheduleOutlined,
  UserOutlined,
  LogoutOutlined,
  DollarOutlined,
  CreditCardOutlined,
  AuditOutlined,
  TableOutlined,
  CheckCircleOutlined,
  WalletOutlined,
  BellOutlined,
  HistoryOutlined,
  DownloadOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { notificationApi } from '../api'

const { Header, Sider, Content } = AntLayout

const menuItems: MenuProps['items'] = [
  { key: '/dashboard', icon: <HomeOutlined />, label: '工作台' },
  { key: '/members', icon: <TeamOutlined />, label: '会员管理' },
  { key: '/courses', icon: <CalendarOutlined />, label: '课程管理' },
  { key: '/bookings', icon: <ScheduleOutlined />, label: '预约签到' },
  { key: '/coaches', icon: <UserOutlined />, label: '教练管理' },
  { key: '/orders', icon: <DollarOutlined />, label: '订单管理' },
  { key: '/subscriptions', icon: <CreditCardOutlined />, label: '订阅管理' },
  { key: '/leads', icon: <AuditOutlined />, label: '潜客管理' },
  { key: '/campaigns', icon: <AuditOutlined />, label: '营销活动' },
  { key: '/schedules', icon: <TableOutlined />, label: '排课日历' },
  { key: '/checkin', icon: <CheckCircleOutlined />, label: '签到中心' },
  { key: '/cards', icon: <WalletOutlined />, label: '会员卡管理' },
  { key: '/audit-logs', icon: <HistoryOutlined />, label: '操作日志' },
  { key: '/export', icon: <DownloadOutlined />, label: '数据导出' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
]

const Layout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [unreadCount, setUnreadCount] = useState(0)

  const stored = localStorage.getItem('user')
  const currentUser = stored ? JSON.parse(stored) : null

  const fetchUnread = async () => {
    try {
      const res = await notificationApi.getUnreadCount()
      setUnreadCount(res.count)
    } catch { /* ignore */ }
  }

  useEffect(() => { fetchUnread(); const t = setInterval(fetchUnread, 30000); return () => clearInterval(t) }, [])

  const handleMenuClick: MenuProps['onClick'] = (e) => { navigate(e.key) }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const logoutItems: MenuProps['items'] = [
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider width={200}>
        <div style={{
          height: 64, margin: 16,
          background: 'rgba(255, 255, 255, 0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontWeight: 'bold',
        }}>
          健身管理系统
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={menuItems} onClick={handleMenuClick} />
      </Sider>
      <AntLayout>
        <Header style={{
          padding: '0 24px', background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <h2 style={{ margin: 0 }}>健身瑜伽教培管理系统</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Badge count={unreadCount} overflowCount={99} size="small">
              <BellOutlined
                style={{ fontSize: 20, cursor: 'pointer' }}
                onClick={() => navigate('/notifications')}
              />
            </Badge>
            <Dropdown menu={{ items: logoutItems }} placement="bottomRight">
              <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span style={{ marginLeft: 8 }}>{currentUser?.username || '管理员'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, background: '#fff', minHeight: 360 }}>
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
