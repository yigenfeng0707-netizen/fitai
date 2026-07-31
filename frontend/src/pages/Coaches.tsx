import { Table, Button, Space, Modal, Form, Input, Switch, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { coachApi } from '../api'
import type { Coach, CoachCreate, ListResponse } from '../api/types'

const Coaches = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCoach, setEditingCoach] = useState<Coach | null>(null)
  const [data, setData] = useState<Coach[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [form] = Form.useForm()

  const fetchData = async (p = page, ps = pageSize) => {
    setLoading(true)
    try {
      const res = await coachApi.getList({ skip: (p - 1) * ps, limit: ps })
      setData((res as ListResponse<Coach>).data)
      setTotal((res as ListResponse<Coach>).total)
    } catch (error) {
      message.error('获取教练列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreate = () => {
    setEditingCoach(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (record: Coach) => {
    setEditingCoach(record)
    form.setFieldsValue(record)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await coachApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingCoach) {
        await coachApi.update(editingCoach.id, values)
        message.success('更新成功')
      } else {
        await coachApi.create(values as CoachCreate)
        message.success('创建成功')
      }
      setIsModalOpen(false)
      fetchData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '专长', dataIndex: 'specialization', key: 'specialization' },
    { title: '总课时', dataIndex: 'total_hours', key: 'total_hours', render: (v: number) => `${v}小时` },
    { title: '服务学员', dataIndex: 'total_students', key: 'total_students' },
    { title: '评分', dataIndex: 'avg_rating', key: 'avg_rating', render: (v: number) => (v ?? 0).toFixed(1) },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? '在职' : '离职' },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Coach) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1>教练管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增教练
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => { setPage(p); setPageSize(ps); fetchData(p, ps) },
        }}
      />

      <Modal
        title={editingCoach ? '编辑教练' : '新增教练'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="specialization" label="专长">
            <Input placeholder="如：哈他瑜伽、普拉提" />
          </Form.Item>
          <Form.Item name="introduction" label="简介">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="is_active" label="在职状态" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="在职" unCheckedChildren="离职" />
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

export default Coaches
