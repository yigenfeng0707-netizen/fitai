import { useState, useEffect } from 'react'
import {
  Card, Row, Col, Statistic, Table, Tag, Button, message, Space, Input,
} from 'antd'
import {
  CheckCircleOutlined, ClockCircleOutlined, TeamOutlined, UserOutlined,
  ScanOutlined, SearchOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { bookingApi } from '../api'
import type { CheckinTodayData, CheckinBookingItem } from '../api/booking'

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'blue', text: '待确认' },
  confirmed: { color: 'green', text: '已确认' },
  checked_in: { color: 'success', text: '已签到' },
  cancelled: { color: 'default', text: '已取消' },
  no_show: { color: 'error', text: '旷课' },
}

const CheckinCenter = () => {
  const [data, setData] = useState<CheckinTodayData | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [checkingIn, setCheckingIn] = useState<number | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await bookingApi.getCheckinToday()
      setData(res)
    } catch {
      message.error('获取签到数据失败')
    }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleCheckIn = async (bookingId: number) => {
    setCheckingIn(bookingId)
    try {
      await bookingApi.checkIn(bookingId, 'manual')
      message.success('签到成功')
      fetchData()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '签到失败')
    }
    setCheckingIn(null)
  }

  const filteredSchedules = data?.schedules
    .map((s) => ({
      ...s,
      bookings: searchText
        ? s.bookings.filter(
            (b) =>
              b.member_name.includes(searchText) || b.member_phone.includes(searchText)
          )
        : s.bookings,
    }))
    .filter((s) => s.bookings.length > 0 || !searchText) ?? []

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="今日预约"
              value={data?.total ?? 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="已签到"
              value={data?.checked_in ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="待签到"
              value={(data?.pending ?? 0) + (data?.confirmed ?? 0)}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="已取消"
              value={data?.cancelled ?? 0}
              suffix={`/ ${data?.no_show ?? 0} 旷课`}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="签到率"
              value={data && data.total > 0 ? ((data.checked_in / data.total) * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ color: data && data.total > 0 && (data.checked_in / data.total) > 0.8 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="课次数"
              value={data?.schedules.length ?? 0}
              prefix={<ScanOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <ScanOutlined />
            <span>今日签到管理</span>
            <small style={{ color: '#999', fontWeight: 'normal' }}>
              {dayjs().format('YYYY年MM月DD日 dddd')}
            </small>
          </Space>
        }
        extra={
          <Input
            placeholder="搜索会员姓名/手机号"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 240 }}
            allowClear
          />
        }
      >
        {filteredSchedules.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            <ScanOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>今日暂无排课或预约</p>
          </div>
        )}

        {filteredSchedules.map((schedule) => (
          <Card
            key={schedule.schedule_id}
            type="inner"
            size="small"
            title={
              <Space>
                <Tag color="blue">{schedule.course_name}</Tag>
                <span style={{ color: '#666' }}>
                  {dayjs(schedule.start_time).format('HH:mm')} - {dayjs(schedule.end_time).format('HH:mm')}
                </span>
              </Space>
            }
            extra={
              <Space>
                <UserOutlined />
                <span>{schedule.checked_in_count}/{schedule.enrolled_count} 已签到</span>
              </Space>
            }
            style={{ marginBottom: 12 }}
          >
            <Table
              dataSource={schedule.bookings}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: '会员',
                  dataIndex: 'member_name',
                  key: 'member_name',
                  width: 120,
                },
                {
                  title: '手机号',
                  dataIndex: 'member_phone',
                  key: 'member_phone',
                  width: 140,
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  width: 100,
                  render: (v: string) => {
                    const m = statusMap[v]
                    return m ? <Tag color={m.color}>{m.text}</Tag> : v
                  },
                },
                {
                  title: '签到时间',
                  dataIndex: 'check_in_time',
                  key: 'check_in_time',
                  width: 160,
                  render: (v?: string) => (v ? dayjs(v).format('HH:mm:ss') : '-'),
                },
                {
                  title: '操作',
                  key: 'actions',
                  width: 120,
                  render: (_: any, record: CheckinBookingItem) => (
                    record.status === 'checked_in' ? (
                      <Tag color="success">已签到</Tag>
                    ) : record.status === 'cancelled' ? (
                      <Tag color="default">已取消</Tag>
                    ) : (
                      <Button
                        type="primary"
                        size="small"
                        icon={<CheckCircleOutlined />}
                        loading={checkingIn === record.id}
                        onClick={() => handleCheckIn(record.id)}
                      >
                        签到
                      </Button>
                    )
                  ),
                },
              ]}
            />
          </Card>
        ))}
      </Card>
    </div>
  )
}

export default CheckinCenter
