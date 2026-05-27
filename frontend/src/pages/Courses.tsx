import { Table, Button, Space, Modal, Form, Input, InputNumber, Select, message, Popconfirm, Tabs } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { courseApi } from '../api'
import type { Course, CourseCreate, CourseSchedule, ScheduleCreate, ListResponse } from '../api/types'

const Courses = () => {
  const [isCourseModalOpen, setIsCourseModalOpen] = useState(false)
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [schedules, setSchedules] = useState<CourseSchedule[]>([])
  const [loading, setLoading] = useState(false)
  const [courseForm] = Form.useForm()
  const [scheduleForm] = Form.useForm()

  const fetchCourses = async () => {
    setLoading(true)
    try {
      const res = await courseApi.getList({ limit: 100 })
      setCourses((res as ListResponse<Course>).data)
    } catch (error) {
      message.error('获取课程列表失败')
    }
    setLoading(false)
  }

  const fetchSchedules = async () => {
    try {
      const res = await courseApi.getSchedules({ limit: 100 })
      setSchedules((res as ListResponse<CourseSchedule>).data)
    } catch (error) {
      message.error('获取排期列表失败')
    }
  }

  useEffect(() => {
    fetchCourses()
    fetchSchedules()
  }, [])

  const handleCreateCourse = () => {
    setEditingCourse(null)
    courseForm.resetFields()
    setIsCourseModalOpen(true)
  }

  const handleEditCourse = (record: Course) => {
    setEditingCourse(record)
    courseForm.setFieldsValue(record)
    setIsCourseModalOpen(true)
  }

  const handleDeleteCourse = async (id: number) => {
    try {
      await courseApi.delete(id)
      message.success('删除成功')
      fetchCourses()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleCourseSubmit = async (values: any) => {
    try {
      if (editingCourse) {
        await courseApi.update(editingCourse.id, values)
        message.success('更新成功')
      } else {
        await courseApi.create(values as CourseCreate)
        message.success('创建成功')
      }
      setIsCourseModalOpen(false)
      fetchCourses()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleCreateSchedule = () => {
    scheduleForm.resetFields()
    setIsScheduleModalOpen(true)
  }

  const handleScheduleSubmit = async (values: any) => {
    try {
      await courseApi.createSchedule(values as ScheduleCreate)
      message.success('创建排期成功')
      setIsScheduleModalOpen(false)
      fetchSchedules()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }

  const courseColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '课程名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'course_type', key: 'course_type', render: (v: string) => v === 'group' ? '团课' : '私教' },
    { title: '时长', dataIndex: 'duration_minutes', key: 'duration_minutes', render: (v: number) => `${v}分钟` },
    { title: '教室', dataIndex: 'room', key: 'room' },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v: number) => `¥${v}` },
    { title: '最大人数', dataIndex: 'max_attendees', key: 'max_attendees' },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? '启用' : '停用' },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Course) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditCourse(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteCourse(record.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const scheduleColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '课程ID', dataIndex: 'course_id', key: 'course_id' },
    { title: '开始时间', dataIndex: 'start_time', key: 'start_time' },
    { title: '结束时间', dataIndex: 'end_time', key: 'end_time' },
    { title: '已报名', dataIndex: 'enrolled_count', key: 'enrolled_count' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const map: Record<string, string> = { scheduled: '已排期', completed: '已完成', cancelled: '已取消' }
      return map[v] || v
    }},
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>课程管理</h1>
      
      <Tabs
        items={[
          {
            key: 'courses',
            label: '课程列表',
            children: (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateCourse}>
                    新增课程
                  </Button>
                </div>
                <Table columns={courseColumns} dataSource={courses} rowKey="id" loading={loading} />
              </>
            ),
          },
          {
            key: 'schedules',
            label: '课程排期',
            children: (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSchedule}>
                    新增排期
                  </Button>
                </div>
                <Table columns={scheduleColumns} dataSource={schedules} rowKey="id" />
              </>
            ),
          },
        ]}
      />

      <Modal
        title={editingCourse ? '编辑课程' : '新增课程'}
        open={isCourseModalOpen}
        onCancel={() => setIsCourseModalOpen(false)}
        footer={null}
      >
        <Form form={courseForm} layout="vertical" onFinish={handleCourseSubmit}>
          <Form.Item name="name" label="课程名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="course_type" label="类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="group">团课</Select.Option>
              <Select.Option value="private">私教</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="duration_minutes" label="时长(分钟)" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="room" label="教室">
            <Input />
          </Form.Item>
          <Form.Item name="price" label="价格" rules={[{ required: true }]}>
            <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="max_attendees" label="最大人数" initialValue={15}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交</Button>
              <Button onClick={() => setIsCourseModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增课程排期"
        open={isScheduleModalOpen}
        onCancel={() => setIsScheduleModalOpen(false)}
        footer={null}
      >
        <Form form={scheduleForm} layout="vertical" onFinish={handleScheduleSubmit}>
          <Form.Item name="course_id" label="课程" rules={[{ required: true }]}>
            <Select>
              {courses.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="start_time" label="开始时间" rules={[{ required: true }]}>
            <Input type="datetime-local" />
          </Form.Item>
          <Form.Item name="end_time" label="结束时间" rules={[{ required: true }]}>
            <Input type="datetime-local" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">提交</Button>
              <Button onClick={() => setIsScheduleModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Courses
