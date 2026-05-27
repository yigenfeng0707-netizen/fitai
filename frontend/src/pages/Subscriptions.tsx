import { Table, Button, Tag, Form, InputNumber, Select, Switch, message, Modal, Space } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { subscriptionApi } from '../api/subscription'
import type { Subscription } from '../api/types'

const planMap: Record<string, { color: string; text: string }> = {
  free: { color: 'default', text: '免费版' },
  basic: { color: 'blue', text: '基础版' },
  pro: { color: 'purple', text: '专业版' },
  enterprise: { color: 'gold', text: '企业版' },
}

const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: 'green', text: '生效中' },
  expired: { color: 'red', text: '已过期' },
  cancelled: { color: 'default', text: '已取消' },
  pending: { color: 'orange', text: '待激活' },
}

const F = (v: number | null | undefined) => `¥${(v ?? 0).toFixed(2)}`

const Subscriptions = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchSubscriptions = async () => {
    setLoading(true)
    try {
      const res = await subscriptionApi.getList({ limit: 100 })
      setSubscriptions(res.data)
    } catch {
      message.error('获取订阅列表失败')
    }
    setLoading(false)
  }

  useEffect(() => { fetchSubscriptions() }, [])

  const handleCreate = () => {
    form.resetFields()
    form.setFieldsValue({ plan: 'basic', amount: 99, auto_renew: true })
    setModalOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      await subscriptionApi.create(values.plan, values.amount, values.auto_renew)
      message.success('创建成功')
      setModalOpen(false)
      fetchSubscriptions()
    } catch {
      message.error('创建失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '套餐', dataIndex: 'plan', key: 'plan',
      render: (v: string) => { const m = planMap[v]; return m ? <Tag color={m.color}>{m.text}</Tag> : v },
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (v: string) => { const m = statusMap[v]; return m ? <Tag color={m.color}>{m.text}</Tag> : v },
    },
    { title: '开始时间', dataIndex: 'start_date', key: 'start_date' },
    { title: '结束时间', dataIndex: 'end_date', key: 'end_date' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => F(v) },
    { title: '实付', dataIndex: 'actual_amount', key: 'actual_amount', render: (v: number) => F(v) },
    {
      title: '自动续费', dataIndex: 'auto_renew', key: 'auto_renew',
      render: (v: boolean) => (v ? <Tag color="green">开启</Tag> : <Tag>关闭</Tag>),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>订阅管理</h2>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建订阅</Button>
      </div>
      <Table columns={columns} dataSource={subscriptions} rowKey="id" loading={loading} pagination={{ pageSize: 20, showSizeChanger: true }} />

      <Modal title="新建订阅" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="plan" label="套餐" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="free">免费版</Select.Option>
              <Select.Option value="basic">基础版</Select.Option>
              <Select.Option value="pro">专业版</Select.Option>
              <Select.Option value="enterprise">企业版</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="amount" label="金额" rules={[{ required: true }]}>
            <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="auto_renew" label="自动续费" valuePropName="checked">
            <Switch checkedChildren="开" unCheckedChildren="关" />
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

export default Subscriptions
