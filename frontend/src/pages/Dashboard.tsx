import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Tag } from 'antd'
import { UserOutlined, TeamOutlined, BookOutlined, CalendarOutlined, DollarOutlined, RiseOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { analyticsApi, aiApi } from '../api'
import type { AnalyticsDashboard, DashboardInsights } from '../api/types'

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

  if (loading) return <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>加载中...</div>
  if (!data) return <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>暂无数据</div>

  const { revenue, members, bookings, courses, coaches } = data

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>经营分析大屏</h1>

      {/* 概览统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={8} md={4}>
          <Card loading={loading}><Statistic title="今日营收" value={revenue.today} prefix={<DollarOutlined />} precision={0} suffix="元" /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="本月营收" value={revenue.month} prefix={<RiseOutlined />} precision={0} suffix="元" valueStyle={{ color: '#3f8600' }} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="本月增长率" value={revenue.month_growth} precision={1} suffix="%" prefix={revenue.month_growth >= 0 ? <RiseOutlined /> : undefined} valueStyle={{ color: revenue.month_growth >= 0 ? '#3f8600' : '#cf1322' }} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="会员总数" value={members.total} prefix={<UserOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="活跃会员" value={members.active} prefix={<TeamOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="本月新增" value={members.new_month} prefix={<UserOutlined />} suffix="人" valueStyle={{ color: '#1890ff' }} /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="今日预约" value={bookings.today} prefix={<CalendarOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="已签到" value={bookings.checked_in_today} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#1890ff' }} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="本周预约" value={bookings.week} prefix={<BookOutlined />} /></Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card><Statistic title="30天上课率" value={bookings.completion_rate} prefix={<ClockCircleOutlined />} precision={1} suffix="%" /></Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="收入趋势 (近30天)" size="small">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={revenue.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`¥${val}`, '营收']} />
                <Line type="monotone" dataKey="revenue" stroke="#1890ff" strokeWidth={2} dot={false} name="营收" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="会员增长趋势 (近30天)" size="small">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={members.trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}人`, '新增']} />
                <Line type="monotone" dataKey="count" stroke="#52c41a" strokeWidth={2} dot={false} name="新增会员" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="热门课程 Top5 (近30天)" size="small">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={courses.top} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}次`, '预约次数']} />
                <Bar dataKey="booking_count" fill="#1890ff" name="预约次数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="时段分布 (今日)" size="small">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={bookings.hour_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}次`, '预约']} />
                <Bar dataKey="count" fill="#722ed1" name="预约数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="教练工作量 (本周)" size="small">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={coaches.week_load} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(val: any) => [`${val}节`, '课程数']} />
                <Bar dataKey="class_count" fill="#fa8c16" name="课程数" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="AI 经营洞察" size="small">
            {insights?.insights && insights.insights.length > 0 ? (
              insights.insights.map((item, idx) => (
                <div key={idx} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <Tag color="purple">AI</Tag> {item}
                </div>
              ))
            ) : (
              <span style={{ color: '#999' }}>暂无洞察数据</span>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
