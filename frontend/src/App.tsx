import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Members from './pages/Members'
import Courses from './pages/Courses'
import Bookings from './pages/Bookings'
import Coaches from './pages/Coaches'
import Orders from './pages/Orders'
import Subscriptions from './pages/Subscriptions'
import PaymentResult from './pages/PaymentResult'
import BodyTest from './pages/BodyTest'
import Leads from './pages/Leads'
import Schedule from './pages/Schedule'
import CheckinCenter from './pages/CheckinCenter'
import MemberCard from './pages/MemberCard'
import Cards from './pages/Cards'
import Notifications from './pages/Notifications'
import AuditLogs from './pages/AuditLogs'
import DataExport from './pages/DataExport'
import Settings from './pages/Settings'
import Campaigns from './pages/Campaigns'
import Automations from './pages/Automations'
import Coupons from './pages/Coupons'
import Layout from './components/Layout'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token && location.pathname !== '/login') {
      navigate('/login', { replace: true })
    }
  }, [navigate, location.pathname])

  return <>{children}</>
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <RequireAuth>
              <ErrorBoundary>
                <Layout />
              </ErrorBoundary>
            </RequireAuth>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="members" element={<Members />} />
            <Route path="courses" element={<Courses />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="coaches" element={<Coaches />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:orderId/result" element={<PaymentResult />} />
            <Route path="subscriptions" element={<Subscriptions />} />
            <Route path="body-test/:memberId" element={<BodyTest />} />
            <Route path="leads" element={<Leads />} />
            <Route path="schedules" element={<Schedule />} />
            <Route path="checkin" element={<CheckinCenter />} />
            <Route path="member-card/:memberId" element={<MemberCard />} />
            <Route path="cards" element={<Cards />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="audit-logs" element={<AuditLogs />} />
            <Route path="export" element={<DataExport />} />
            <Route path="campaigns" element={<Campaigns />} />
            <Route path="automations" element={<Automations />} />
            <Route path="coupons" element={<Coupons />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
