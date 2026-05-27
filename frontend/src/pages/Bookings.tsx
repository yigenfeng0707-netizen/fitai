import { Table, Button, Space, Tag, Modal, Form, Select, Input, message } from 'antd'
import { PlusOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { bookingApi, memberApi, courseApi } from '../api'
import type { Booking, BookingCreate, Member, CourseSchedule, ListResponse } from '../api/types'

const Bookings = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [bookings, setBookings] = useState<Booking[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [schedules, setSchedules] = useState<CourseSchedule[]>([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const [bookingRes, memberRes, scheduleRes] = await Promise.all([
        bookingApi.getList({ limit: 100 }),
        memberApi.getList({ limit: 100 }),
        courseApi.getSchedules({ limit: 100 }),
      ])
      setBookings((bookingRes as ListResponse<Booking>).data)
      setMembers((memberRes as ListResponse<Member>).data)
      setSchedules((scheduleRes as ListResponse<CourseSchedule>).data)
    } catch (error) {
      message.error('获取数据失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreate = () => {
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      await bookingApi.create(values as BookingCreate)
      message.success('预约成功')
      setIsModalOpen(false)
      fetchData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '预约失败')
    }
  }

  const handleCheckIn = async (id: number) => {
    try {
      await bookingApi.checkIn(id, 'manual')
      message.success('签到成功')
      fetchData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '签到失败')
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await bookingApi.cancel(id)
      message.success('取消成功')
      fetchData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消失败')
    }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    pending: { color: 'blue', text: '待确认' },
    confirmed: { color: 'green', text: '已确认' },
    checked_in: { color: 'success', text: '已签到' },
    cancelled: { color: 'error', text: '已取消' },
    no_show: { color: 'default', text: '旷课' },
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '会员ID', dataIndex: 'member_id', key: 'member_id' },
    { title: '排期ID', dataIndex: 'schedule_id', key: 'schedule_id' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const item = statusMap[v] || { color: 'default', text: v }
      return <Tag color={item.color}>{item.text}</Tag>
    }},
    { title: '签到时间', dataIndex: 'check_in_time', key: 'check_in_time', render: (v: string) => v || '-' },
    { title: '备注', dataIndex: 'notes', key: 'notes', render: (v: string) => v || '-' },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Booking) => (
        <Space>
          {(record.status === 'pending' || record.status === 'confirmed') && (
            <>
              <Button icon={<CheckOutlined />} size="small" type="primary" onClick={() => handleCheckIn(record.id)}>
                签到
              </Button>
              <Button icon={<CloseOutlined />} size="small" danger onClick={() => handleCancel(record.id)}>
                取消
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1>预约签到</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建预约
        </Button>
      </div>

      <Table columns={columns} dataSource={bookings} rowKey="id" loading={loading} />

      <Modal
        title="新建预约"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="member_id" label="会员" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="children" placeholder="选择会员">
              {members.map(m => (
                <Select.Option key={m.id} value={m.id}>{m.name} ({m.phone})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="schedule_id" label="课程排期" rules={[{ required: true }]}>
            <Select placeholder="选择排期">
              {schedules.map(s => (
                <Select.Option key={s.id} value={s.id}>
                  排期#{s.id} - {s.start_time} (已报名: {s.enrolled_count})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交</Button>
              <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Bookings
