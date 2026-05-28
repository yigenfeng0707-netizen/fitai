import { Table, Button, Space, Tag, Select, message, Popconfirm, Modal, Form, Input, InputNumber, DatePicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { campaignApi } from '../api/campaign'
import type { Campaign, CampaignCreate, CampaignUpdate } from '../api/campaign'

const statusMap: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  active: { color: 'green', text: '进行中' },
  paused: { color: 'orange', text: '已暂停' },
  completed: { color: 'blue', text: '已完成' },
  cancelled: { color: 'red', text: '已取消' },
}

const typeMap: Record<string, string> = {
  promotion: '促销活动',
  event: '活动邀约',
  reminder: '续费提醒',
  reactivation: '沉睡唤醒',
  holiday: '节日营销',
}

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null)
  const [form] = Form.useForm()

  const fetchCampaigns = async (p = page) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { skip: (p - 1) * 20, limit: 20 }
      if (statusFilter) params.status = statusFilter
      const res = await campaignApi.getList(params)
      setCampaigns(res.data)
      setTotal(res.total)
    } catch {
      message.error('获取营销活动列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchCampaigns()
  }, [statusFilter])

  const handleCreate = () => {
    setEditingCampaign(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: Campaign) => {
    setEditingCampaign(record)
    form.setFieldsValue({
      ...record,
      start_date: record.start_date ? undefined : undefined,
      end_date: record.end_date ? undefined : undefined,
    })
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await campaignApi.delete(id)
      message.success('删除成功')
      fetchCampaigns()
    } catch {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        start_date: values.start_date?.toISOString(),
        end_date: values.end_date?.toISOString(),
        channels: values.channels ? values.channels.split(',').map((s: string) => s.trim()) : undefined,
      }
      if (editingCampaign) {
        await campaignApi.update(editingCampaign.id, data as CampaignUpdate)
        message.success('更新成功')
      } else {
        await campaignApi.create(data as CampaignCreate)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchCampaigns()
    } catch (err: any) {
      message.error(err.response?.data?.detail || '操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '活动名称', dataIndex: 'name', key: 'name' },
    {
      title: '类型',
      dataIndex: 'campaign_type',
      key: 'campaign_type',
      render: (v: string) => typeMap[v] || v,
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
    { title: '目标人数', dataIndex: 'target_count', key: 'target_count' },
    { title: '已发送', dataIndex: 'sent_count', key: 'sent_count' },
    { title: '已打开', dataIndex: 'opened_count', key: 'opened_count' },
    { title: '已转化', dataIndex: 'converted_count', key: 'converted_count' },
    { title: '预算(元)', dataIndex: 'budget', key: 'budget', render: (v: number) => `¥${v}` },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Campaign) => (
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
        <h1>营销活动</h1>
        <Space>
          <span>状态:</span>
          <Select
            allowClear
            placeholder="全部"
            style={{ width: 120 }}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
            options={[
              { value: 'draft', label: '草稿' },
              { value: 'active', label: '进行中' },
              { value: 'paused', label: '已暂停' },
              { value: 'completed', label: '已完成' },
              { value: 'cancelled', label: '已取消' },
            ]}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新增活动
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={campaigns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: 20,
          total,
          showSizeChanger: false,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p) => { setPage(p); fetchCampaigns(p) },
        }}
      />

      <Modal
        title={editingCampaign ? '编辑活动' : '新增活动'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="活动名称" rules={[{ required: true, message: '请输入活动名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="campaign_type" label="活动类型" initialValue="promotion">
            <Select>
              <Select.Option value="promotion">促销活动</Select.Option>
              <Select.Option value="event">活动邀约</Select.Option>
              <Select.Option value="reminder">续费提醒</Select.Option>
              <Select.Option value="reactivation">沉睡唤醒</Select.Option>
              <Select.Option value="holiday">节日营销</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="channels" label="推送渠道(逗号分隔)">
            <Input placeholder="例如: sms,email,wechat" />
          </Form.Item>
          <Form.Item name="target_count" label="目标人数">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="budget" label="预算(元)">
            <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="start_date" label="开始时间">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="end_date" label="结束时间">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
          {editingCampaign && (
            <>
              <Form.Item name="actual_cost" label="实际成本(元)">
                <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="sent_count" label="已发送数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="opened_count" label="已打开数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="converted_count" label="已转化数">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="converted_revenue" label="转化收入(元)">
                <InputNumber prefix="¥" min={0} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}
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

export default Campaigns
