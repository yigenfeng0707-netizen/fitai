import { Table, Button, Space, Tag, Select, message, Popconfirm, Modal, Form, Input, InputNumber } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { leadApi } from '../api'
import type { Lead, LeadCreate, LeadUpdate } from '../api/types'

const sourceMap: Record<string, { color: string; text: string }> = {
  call: { color: 'blue', text: '电话咨询' },
  visit: { color: 'cyan', text: '到店' },
  referral: { color: 'green', text: '推荐' },
  ad: { color: 'purple', text: '广告' },
  social: { color: 'geekblue', text: '社交媒体' },
  other: { color: 'default', text: '其他' },
}

const statusMap: Record<string, { color: string; text: string }> = {
  new: { color: 'orange', text: '新潜客' },
  contacted: { color: 'blue', text: '已联系' },
  qualified: { color: 'purple', text: '已确认' },
  converted: { color: 'green', text: '已转化' },
  lost: { color: 'default', text: '已流失' },
}

const intentMap: Record<string, string> = {
  fitness: '健身',
  yoga: '瑜伽',
  training: '教培',
  rehab: '康复',
  other: '其他',
}

const Leads = () => {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingLead, setEditingLead] = useState<Lead | null>(null)
  const [form] = Form.useForm()

  const fetchLeads = async (p = page) => {
    setLoading(true)
    try {
      const params: any = { skip: (p - 1) * 20, limit: 20 }
      if (statusFilter) params.status = statusFilter
      const res = await leadApi.getList(params)
      setLeads(res.data)
      setTotal(res.total)
    } catch {
      message.error('获取潜客列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchLeads()
  }, [statusFilter])

  const handleCreate = () => {
    setEditingLead(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: Lead) => {
    setEditingLead(record)
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await leadApi.delete(id)
      message.success('删除成功')
      fetchLeads()
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingLead) {
        await leadApi.update(editingLead.id, values as LeadUpdate)
        message.success('更新成功')
      } else {
        await leadApi.create(values as LeadCreate)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchLeads()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '电话', dataIndex: 'phone', key: 'phone' },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      render: (v: string) => {
        const m = sourceMap[v]
        return m ? <Tag color={m.color}>{m.text}</Tag> : v
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => {
        const m = statusMap[v]
        return m ? <Tag color={m.color}>{m.text}</Tag> : v
      },
    },
    {
      title: '意向',
      dataIndex: 'intent',
      key: 'intent',
      render: (v?: string) => (v ? intentMap[v] || v : '-'),
    },
    { title: '跟进次数', dataIndex: 'follow_up_count', key: 'follow_up_count' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_: any, record: Lead) => (
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
        <h1>潜客管理</h1>
        <Space>
          <span>状态:</span>
          <Select
            allowClear
            placeholder="全部"
            style={{ width: 120 }}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
            options={[
              { value: 'new', label: '新潜客' },
              { value: 'contacted', label: '已联系' },
              { value: 'qualified', label: '已确认' },
              { value: 'converted', label: '已转化' },
              { value: 'lost', label: '已流失' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新增潜客
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={leads}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: 20,
          total,
          showSizeChanger: false,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p) => { setPage(p); fetchLeads(p) },
        }}
      />

      <Modal
        title={editingLead ? '编辑潜客' : '新增潜客'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={520}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="gender" label="性别">
            <Select allowClear>
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="age" label="年龄">
            <InputNumber min={1} max={120} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="source" label="来源" initialValue="visit">
            <Select>
              <Select.Option value="call">电话咨询</Select.Option>
              <Select.Option value="visit">到店</Select.Option>
              <Select.Option value="referral">推荐</Select.Option>
              <Select.Option value="ad">广告</Select.Option>
              <Select.Option value="social">社交媒体</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="intent" label="意向">
            <Select allowClear>
              <Select.Option value="fitness">健身</Select.Option>
              <Select.Option value="yoga">瑜伽</Select.Option>
              <Select.Option value="training">教培</Select.Option>
              <Select.Option value="rehab">康复</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="expected_budget" label="预算(元)">
            <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
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

export default Leads
