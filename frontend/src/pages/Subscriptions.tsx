import { Table, Button, Tag, Form, InputNumber, Select, Switch, message, Modal, Space } from 'antd'
import { PlusOutlined, StopOutlined, ReloadOutlined, ArrowUpOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { subscriptionApi } from '../api/subscription'

const planMap: Record<string, { color: string; text: string }> = {
  trial: { color: 'default', text: '试用版' },
  basic: { color: 'blue', text: '基础版' },
  professional: { color: 'purple', text: '专业版' },
  enterprise: { color: 'gold', text: '企业版' },
  free: { color: 'default', text: '免费版' },
  pro: { color: 'purple', text: '专业版' },
}

const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: 'green', text: '生效中' },
  expired: { color: 'red', text: '已过期' },
  cancelled: { color: 'default', text: '已取消' },
  pending: { color: 'orange', text: '待激活' },
}

const F = (v: number | null | undefined) => `¥${(v ?? 0).toFixed(2)}`

const Subscriptions = () => {
  const [subscriptions, setSubscriptions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [selectedSub, setSelectedSub] = useState<any>(null)
  const [form] = Form.useForm()
  const [upgradeForm] = Form.useForm()

  const fetchSubscriptions = async () => {
    setLoading(true)
    try {
      const res = await subscriptionApi.getList({ limit: 100 })
      setSubscriptions(res.data || [])
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

  const handleCancel = async (id: number) => {
    Modal.confirm({
      title: '确认取消此订阅？',
      onOk: async () => {
        try {
          await subscriptionApi.cancel(id)
          message.success('已取消')
          fetchSubscriptions()
        } catch { message.error('取消失败') }
      },
    })
  }

  const handleRenew = async (id: number) => {
    try {
      await subscriptionApi.renew(id, 1, 0)
      message.success('已续费1个月')
      fetchSubscriptions()
    } catch { message.error('续费失败') }
  }

  const handleToggleRenew = async (id: number) => {
    try {
      await subscriptionApi.toggleRenew(id)
      message.success('已切换')
      fetchSubscriptions()
    } catch { message.error('切换失败') }
  }

  const handleUpgrade = (sub: any) => {
    setSelectedSub(sub)
    upgradeForm.resetFields()
    upgradeForm.setFieldsValue({ new_plan: 'professional', duration_months: 0, amount: 0 })
    setUpgradeOpen(true)
  }

  const handleUpgradeSubmit = async (values: any) => {
    if (!selectedSub) return
    try {
      await subscriptionApi.upgrade(selectedSub.id, values.new_plan, values.duration_months, values.amount)
      message.success('升级成功')
      setUpgradeOpen(false)
      fetchSubscriptions()
    } catch { message.error('升级失败') }
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
      render: (v: boolean, record: any) => (
        <Switch
          checked={v}
          size="small"
          onChange={() => handleToggleRenew(record.id)}
          checkedChildren="开"
          unCheckedChildren="关"
        />
      ),
    },
    {
      title: '操作', key: 'actions', width: 200,
      render: (_: any, record: any) => (
        <Space size="small">
          {record.status === 'active' && (
            <>
              <Button size="small" icon={<ArrowUpOutlined />} onClick={() => handleUpgrade(record)}>升级</Button>
              <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRenew(record.id)}>续费</Button>
              <Button size="small" danger icon={<StopOutlined />} onClick={() => handleCancel(record.id)}>取消</Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>订阅管理</h2>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建订阅</Button>
      </div>
      <Table columns={columns} dataSource={subscriptions} rowKey="id" loading={loading} pagination={{ pageSize: 20 }} />

      <Modal title="新建订阅" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="plan" label="套餐" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="trial">试用版 (免费)</Select.Option>
              <Select.Option value="basic">基础版 (¥99/月)</Select.Option>
              <Select.Option value="professional">专业版 (¥299/月)</Select.Option>
              <Select.Option value="enterprise">企业版 (¥899/月)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="amount" label="金额">
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

      <Modal title="升级订阅" open={upgradeOpen} onCancel={() => setUpgradeOpen(false)} footer={null}>
        <Form form={upgradeForm} layout="vertical" onFinish={handleUpgradeSubmit}>
          <Form.Item name="new_plan" label="新套餐" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="basic">基础版 (¥99/月)</Select.Option>
              <Select.Option value="professional">专业版 (¥299/月)</Select.Option>
              <Select.Option value="enterprise">企业版 (¥899/月)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="duration_months" label="额外续期月数 (0=保持剩余天数)">
            <InputNumber min={0} max={12} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="amount" label="金额">
            <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">确认升级</Button>
              <Button onClick={() => setUpgradeOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Subscriptions
