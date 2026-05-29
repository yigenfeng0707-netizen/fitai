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
  ThunderboltOutlined,
  FireOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { notificationApi } from '../api'
import '../styles/theme.css'

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
  { key: '/campaigns', icon: <FireOutlined />, label: '营销活动' },
  { key: '/automations', icon: <ThunderboltOutlined />, label: '营销自动化' },
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
    <AntLayout style={{ minHeight: '100vh', background: 'var(--bg-main)' }}>
      <Sider width={220} style={{ background: 'var(--sidebar-gradient)' }}>
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 900, color: '#fff', fontSize: 16,
            boxShadow: '0 4px 12px rgba(168, 85, 247, 0.4)',
          }}>F</div>
          <span style={{ color: '#fff', fontWeight: 700, fontSize: 17, letterSpacing: 1 }}>FitAI</span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            borderRight: 'none',
            paddingLeft: 8,
            paddingRight: 8,
          }}
        />
      </Sider>
      <AntLayout style={{ background: 'transparent' }}>
        <Header style={{
          padding: '0 32px',
          background: 'var(--glass-bg)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(139, 92, 246, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{
            textAlign: 'center',
            flex: 1,
          }}>
            <h2 style={{
              margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: 2,
              background: 'linear-gradient(135deg, #4c1d95, #6366f1, #a855f7)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>FitAI 智能管理平台</h2>
            <span style={{
              fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, letterSpacing: 1,
            }}>健身瑜伽教培 SaaS 平台</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <Badge count={unreadCount} overflowCount={99} size="small">
              <BellOutlined
                style={{ fontSize: 20, cursor: 'pointer', color: 'var(--text-secondary)' }}
                onClick={() => navigate('/notifications')}
              />
            </Badge>
            <Dropdown menu={{ items: logoutItems }} placement="bottomRight">
              <div style={{
                display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 10,
                padding: '4px 12px 4px 4px', borderRadius: 24,
                background: 'rgba(139, 92, 246, 0.06)',
              }}>
                <Avatar
                  style={{
                    background: 'linear-gradient(135deg, #a855f7, #6366f1)',
                    verticalAlign: 'middle',
                  }}
                  icon={<UserOutlined />}
                />
                <span style={{
                  fontWeight: 500, fontSize: 14, color: 'var(--text-primary)',
                }}>{currentUser?.username || '管理员'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: '20px 24px 0' }}>
          <div style={{
            padding: 28,
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(12px)',
            borderRadius: 'var(--radius-lg)',
            minHeight: 560,
            boxShadow: 'var(--card-shadow)',
            animation: 'fadeInUp 0.4s ease-out',
          }}>
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
