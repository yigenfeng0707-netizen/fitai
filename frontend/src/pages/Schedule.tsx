import { useState, useEffect } from 'react'
import {
  Button, Space, Tag, Modal, Form, Select, DatePicker, TimePicker,
  message, Popconfirm, Card, Row, Col, Statistic, Alert,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined,
  LeftOutlined, RightOutlined, TeamOutlined, CalendarOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

import { scheduleApi, courseApi } from '../api'
import type { CourseSchedule, ScheduleCreate } from '../api/types'

const HOURS = Array.from({ length: 14 }, (_, i) => i + 7)
const DAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const statusColors: Record<string, string> = {
  scheduled: 'blue',
  completed: 'green',
  cancelled: 'default',
}

const statusLabels: Record<string, string> = {
  scheduled: '待上课',
  completed: '已完成',
  cancelled: '已取消',
}

const Schedule = () => {
  const [schedules, setSchedules] = useState<CourseSchedule[]>([])
  const [courses, setCourses] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [weekStart, setWeekStart] = useState(() => dayjs().day(1).startOf('day'))
  const [modalOpen, setModalOpen] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<CourseSchedule | null>(null)
  const [form] = Form.useForm()

  const fetchSchedules = async () => {
    setLoading(true)
    try {
      const start = weekStart.format('YYYY-MM-DDTHH:mm:ss')
      const end = weekStart.add(7, 'day').format('YYYY-MM-DDTHH:mm:ss')
      const res = await scheduleApi.getList({ start_date: start, end_date: end, limit: 200 })
      setSchedules(res.data)
    } catch {
      message.error('获取排期失败')
    }
    setLoading(false)
  }

  const fetchCourses = async () => {
    try {
      const res = await courseApi.getList({ limit: 100 })
      setCourses(res.data)
    } catch {
      message.error('获取课程列表失败')
    }
  }

  useEffect(() => { fetchCourses() }, [])
  useEffect(() => { fetchSchedules() }, [weekStart])

  const prevWeek = () => setWeekStart((prev) => prev.subtract(7, 'day'))
  const nextWeek = () => setWeekStart((prev) => prev.add(7, 'day'))
  const thisWeek = () => setWeekStart(dayjs().day(1).startOf('day'))

  const getDayDate = (offset: number) => weekStart.add(offset, 'day')

  const getScheduleForSlot = (dayOffset: number, hour: number) => {
    const day = getDayDate(dayOffset)
    return schedules.filter((s) => {
      const st = dayjs(s.start_time)
      return st.isSame(day, 'day') && st.hour() === hour
    })
  }

  const getDaySummary = (dayOffset: number) => {
    const day = getDayDate(dayOffset)
    const daySchedules = schedules.filter((s) => dayjs(s.start_time).isSame(day, 'day'))
    return {
      total: daySchedules.length,
      completed: daySchedules.filter((s) => s.status === 'completed').length,
      enrolled: daySchedules.reduce((sum, s) => sum + s.enrolled_count, 0),
    }
  }

  const handleCreate = () => {
    setEditingSchedule(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: CourseSchedule) => {
    setEditingSchedule(record)
    form.setFieldsValue({
      course_id: record.course_id,
      date: dayjs(record.start_time),
      start_time: dayjs(record.start_time),
      end_time: dayjs(record.end_time),
      notes: record.notes,
    })
    setModalOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      const startTime = values.date
        .hour(values.start_time.hour())
        .minute(values.start_time.minute())
        .second(0)
      const endTime = values.date
        .hour(values.end_time.hour())
        .minute(values.end_time.minute())
        .second(0)

      const payload: ScheduleCreate = {
        course_id: values.course_id,
        start_time: startTime.format('YYYY-MM-DDTHH:mm:ss'),
        end_time: endTime.format('YYYY-MM-DDTHH:mm:ss'),
        notes: values.notes,
      }

      if (editingSchedule) {
        await scheduleApi.update(editingSchedule.id, payload)
        message.success('更新成功')
      } else {
        await scheduleApi.create(payload)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchSchedules()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await scheduleApi.delete(id)
      message.success('删除成功')
      fetchSchedules()
    } catch {
      message.error('删除失败')
    }
  }

  const weekSummary = Array.from({ length: 7 }, (_, i) => getDaySummary(i))
  const totalWeek = weekSummary.reduce((s, d) => s + d.total, 0)
  const totalEnrolled = weekSummary.reduce((s, d) => s + d.enrolled, 0)

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic title="本周排课" value={totalWeek} prefix={<CalendarOutlined />} suffix="节" />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="本周预约人次" value={totalEnrolled} prefix={<TeamOutlined />} suffix="人次" />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic title="本周日均" value={totalWeek > 0 ? (totalWeek / 7).toFixed(1) : 0} suffix="节/天" />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="上课率"
              value={totalWeek > 0 ? ((weekSummary.reduce((s, d) => s + d.completed, 0) / totalWeek) * 100).toFixed(0) : 0}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Button icon={<LeftOutlined />} onClick={prevWeek} />
          <Button onClick={thisWeek}>本周</Button>
          <Button icon={<RightOutlined />} onClick={nextWeek} />
          <span style={{ fontWeight: 500, marginLeft: 8 }}>
            {weekStart.format('YYYY年MM月DD日')} - {weekStart.add(6, 'day').format('MM月DD日')}
          </span>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增排课
        </Button>
      </div>

      {schedules.length === 0 && !loading && (
        <Alert
          message="本周暂无排课"
          description={'点击右上角"新增排课"开始安排本周课程'}
          type="info"
          showIcon
          style={{ marginBottom: 16 } as any}
        />
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #f0f0f0', padding: 8, background: '#fafafa', width: 70, textAlign: 'center' }}>时间</th>
              {DAYS.map((day, idx) => (
                <th key={idx} style={{ border: '1px solid #f0f0f0', padding: 8, background: '#fafafa', textAlign: 'center' }}>
                  <div>{day}</div>
                  <small style={{ color: '#999' }}>{getDayDate(idx).format('MM/DD')}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {HOURS.map((hour) => (
              <tr key={hour}>
                <td style={{ border: '1px solid #f0f0f0', padding: 6, textAlign: 'center', color: '#999', fontSize: 12 }}>
                  {`${hour}:00`}
                </td>
                {[0, 1, 2, 3, 4, 5, 6].map((dayOffset) => {
                  const slotSchedules = getScheduleForSlot(dayOffset, hour)
                  return (
                    <td key={dayOffset} style={{ border: '1px solid #f0f0f0', padding: 4, verticalAlign: 'top', minHeight: 60, height: 80 }}>
                      {slotSchedules.length === 0 ? null : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {slotSchedules.map((s) => (
                            <div
                              key={s.id}
                              onClick={() => handleEdit(s)}
                              style={{
                                cursor: 'pointer',
                                fontSize: 12,
                                padding: '3px 5px',
                                borderRadius: 4,
                                background: s.status === 'cancelled' ? '#f5f5f5' : '#e6f7ff',
                                border: s.status === 'cancelled' ? '1px dashed #d9d9d9' : '1px solid #91d5ff',
                              }}
                            >
                              <div style={{ fontWeight: 500, marginBottom: 2 }}>{s.course_name}</div>
                              <div style={{ color: '#666', fontSize: 11 }}>
                                {dayjs(s.start_time).format('HH:mm')} - {dayjs(s.end_time).format('HH:mm')}
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 3 }}>
                                <Tag color={statusColors[s.status]} style={{ fontSize: 10, lineHeight: '16px', margin: 0 }}>
                                  {statusLabels[s.status]}
                                </Tag>
                                <Popconfirm title="确定删除?" onConfirm={() => handleDelete(s.id)}>
                                  <DeleteOutlined style={{ color: '#ff4d4f', fontSize: 11 }} />
                                </Popconfirm>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal
        title={editingSchedule ? '编辑排课' : '新增排课'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={480}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="course_id" label="课程" rules={[{ required: true, message: '请选择课程' }]}>
            <Select
              showSearch
              placeholder="搜索并选择课程"
              filterOption={(input, option) =>
                (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
              }
              options={courses
                .filter((c) => c.is_active)
                .map((c) => ({ value: c.id, label: `${c.name} (${c.course_type === 'group' ? '团课' : '私教'})` }))}
            />
          </Form.Item>
          <Form.Item name="date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Space>
            <Form.Item name="start_time" label="开始时间" rules={[{ required: true, message: '请选择' }]}>
              <TimePicker format="HH:mm" minuteStep={30} />
            </Form.Item>
            <Form.Item name="end_time" label="结束时间" rules={[{ required: true, message: '请选择' }]}>
              <TimePicker format="HH:mm" minuteStep={30} />
            </Form.Item>
          </Space>
          <Form.Item name="notes" label="备注">
            <div />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交</Button>
              <Button onClick={() => setModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Schedule
