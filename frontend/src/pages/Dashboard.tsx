import { useEffect, useState } from 'react'
import { Row, Col, Card, Tag } from 'antd'
import {
  DollarOutlined, RiseOutlined, UserOutlined, TeamOutlined,
  CalendarOutlined, CheckCircleOutlined, BookOutlined, ClockCircleOutlined,
} from '@ant-design/icons'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { analyticsApi, aiApi } from '../api'
import type { AnalyticsDashboard, DashboardInsights } from '../api/types'
import '../styles/theme.css'

const GradientStatCard = ({ title, value, prefix, suffix, color, icon }: any) => (
  <div className="stat-card-gradient fade-in-up" style={{ background: color }}>
    <div className="stat-content">
      <div style={{ opacity: 0.8, fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
        {icon}{title}
      </div>
      <div className="stat-value">
        {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
      </div>
    </div>
  </div>
)

const Dashboard = () => {
  const [data, setData] = useState<AnalyticsDashboard | null>(null)
  const [insights, setInsights] = useState<DashboardInsights | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [dashboardData, aiData] = await Promise.all([
          analyticsApi.getDashboard().catch(() => null),
          aiApi.getInsights().catch(() => null),
        ])
        setData(dashboardData)
        setInsights(aiData)
      } catch (error) {
        console.error('获取经营分析失败:', error)
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  if (loading) return (
    <div style={{ padding: 60, textAlign: 'center' }}>
      <div style={{ fontSize: 14, color: '#8b5cf6', fontWeight: 500 }}>正在加载数据...</div>
    </div>
  )
  if (!data) return (
    <div style={{ padding: 60, textAlign: 'center' }}>
      <div style={{ fontSize: 14, color: '#94a3b8' }}>暂无数据</div>
    </div>
  )

  const { revenue, members, bookings, courses, coaches } = data

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{
            margin: 0, fontSize: 22, fontWeight: 700,
            background: 'linear-gradient(135deg, #4c1d95, #6366f1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>经营分析大屏</h1>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>实时数据概览</span>
        </div>
      </div>

      {/* 渐变统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="今日营收" value={revenue.today} suffix="元"
            color="linear-gradient(135deg, #6366f1, #8b5cf6)" icon={<DollarOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="本月营收" value={revenue.month} suffix="元"
            color="linear-gradient(135deg, #06b6d4, #0ea5e9)" icon={<RiseOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="月增长率" value={revenue.month_growth} suffix="%"
            color="linear-gradient(135deg, #10b981, #059669)" icon={<RiseOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="会员总数" value={members.total}
            color="linear-gradient(135deg, #ec4899, #f43f5e)" icon={<UserOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="活跃会员" value={members.active}
            color="linear-gradient(135deg, #f97316, #f59e0b)" icon={<TeamOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={4}>
          <GradientStatCard title="本月新增" value={members.new_month} suffix="人"
            color="linear-gradient(135deg, #3b82f6, #6366f1)" icon={<UserOutlined />} />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={12} sm={6} md={3}>
          <GradientStatCard title="今日预约" value={bookings.today}
            color="linear-gradient(135deg, #8b5cf6, #a855f7)" icon={<CalendarOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={3}>
          <GradientStatCard title="已签到" value={bookings.checked_in_today}
            color="linear-gradient(135deg, #14b8a6, #06b6d4)" icon={<CheckCircleOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={3}>
          <GradientStatCard title="本周预约" value={bookings.week}
            color="linear-gradient(135deg, #f43f5e, #ec4899)" icon={<BookOutlined />} />
        </Col>
        <Col xs={12} sm={6} md={3}>
          <GradientStatCard title="上课率" value={bookings.completion_rate} suffix="%"
            color="linear-gradient(135deg, #f59e0b, #f97316)" icon={<ClockCircleOutlined />} />
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#6366f1', marginRight: 6 }}>▎</span>收入趋势 (近30天)
            </span>
          }>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={revenue.trend}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0eaff" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(val: any) => [`¥${val}`, '营收']}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e0e0ff', boxShadow: '0 4px 12px rgba(99,102,241,0.1)' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={2.5} fill="url(#colorRevenue)" name="营收" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#10b981', marginRight: 6 }}>▎</span>会员增长趋势 (近30天)
            </span>
          }>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={members.trend}>
                <defs>
                  <linearGradient id="colorMembers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0eaff" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(val: any) => [`${val}人`, '新增']}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e0e0ff', boxShadow: '0 4px 12px rgba(16,185,129,0.1)' }}
                />
                <Area type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2.5} fill="url(#colorMembers)" name="新增会员" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#ec4899', marginRight: 6 }}>▎</span>热门课程 Top5
            </span>
          }>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={courses.top} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0eaff" />
                <XAxis type="number" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(val: any) => [`${val}次`, '预约次数']}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e0e0ff' }}
                />
                <Bar dataKey="booking_count" fill="#ec4899" radius={[0, 6, 6, 0]} name="预约次数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#8b5cf6', marginRight: 6 }}>▎</span>时段分布 (今日)
            </span>
          }>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={bookings.hour_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0eaff" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(val: any) => [`${val}次`, '预约']}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e0e0ff' }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} name="预约数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16, marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#f97316', marginRight: 6 }}>▎</span>教练工作量 (本周)
            </span>
          }>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={coaches.week_load} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0eaff" />
                <XAxis type="number" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(val: any) => [`${val}节`, '课程数']}
                  contentStyle={{ borderRadius: 12, border: '1px solid #e0e0ff' }}
                />
                <Bar dataKey="class_count" fill="#f97316" radius={[0, 6, 6, 0]} name="课程数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              <span style={{ color: '#a855f7', marginRight: 6 }}>▎</span>AI 经营洞察
            </span>
          }>
            {insights?.insights && insights.insights.length > 0 ? (
              insights.insights.map((item, idx) => (
                <div key={idx} style={{
                  padding: '10px 14px', marginBottom: 8,
                  background: 'linear-gradient(135deg, #faf5ff, #f0f0ff)',
                  borderRadius: 10,
                  border: '1px solid rgba(168, 85, 247, 0.1)',
                }}>
                  <Tag color="purple" style={{ borderRadius: 12, marginRight: 6 }}>AI</Tag>
                  <span style={{ color: 'var(--text-primary)' }}>{item}</span>
                </div>
              ))
            ) : (
              <div style={{
                padding: 30, textAlign: 'center',
                color: '#94a3b8', fontSize: 13,
              }}>暂无洞察数据</div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
