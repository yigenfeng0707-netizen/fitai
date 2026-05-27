import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, DashboardOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { memberApi } from '../api'
import type { Member, MemberCreate, ListResponse } from '../api/types'

const Members = () => {
  const navigate = useNavigate()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [data, setData] = useState<Member[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [form] = Form.useForm()

  const fetchData = async (p = page, ps = pageSize) => {
    setLoading(true)
    try {
      const res = await memberApi.getList({ skip: (p - 1) * ps, limit: ps })
      setData((res as ListResponse<Member>).data)
      setTotal((res as ListResponse<Member>).total)
    } catch (error) {
      message.error('获取会员列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreate = () => {
    setEditingMember(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (record: Member) => {
    setEditingMember(record)
    form.setFieldsValue(record)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await memberApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingMember) {
        await memberApi.update(editingMember.id, values)
        message.success('更新成功')
      } else {
        await memberApi.create(values as MemberCreate)
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
    { title: '卡类型', dataIndex: 'card_type', key: 'card_type', render: (v: string) => v === 'monthly' ? '月卡' : v === 'yearly' ? '年卡' : v === 'single' ? '次卡' : '-' },
    { title: '剩余次数', dataIndex: 'card_remaining_count', key: 'card_remaining_count' },
    { title: '等级', dataIndex: 'level', key: 'level' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => v === 'active' ? '正常' : '异常' },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Member) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
          <Button icon={<DashboardOutlined />} size="small" onClick={() => navigate(`/body-test/${record.id}`)}>体测</Button>
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
        <h1>会员管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增会员
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
        title={editingMember ? '编辑会员' : '新增会员'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号" rules={[{ required: true, message: '请输入手机号' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="gender" label="性别">
            <Select allowClear>
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="card_type" label="卡类型">
            <Select allowClear>
              <Select.Option value="single">次卡</Select.Option>
              <Select.Option value="monthly">月卡</Select.Option>
              <Select.Option value="yearly">年卡</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
              <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Members
