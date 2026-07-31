import { Table, Button, Tag, Form, Input, InputNumber, Select, DatePicker, message, Modal, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, StopOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { couponApi } from '../api/coupon'

const F = (v: number | null | undefined) => `¥${(v ?? 0).toFixed(2)}`

const Coupons = () => {
  const [coupons, setCoupons] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await couponApi.getList({ limit: 100 })
      setCoupons(res.data || [])
    } catch { message.error('获取优惠券失败') }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleCreate = () => {
    form.resetFields()
    form.setFieldsValue({ coupon_type: 'fixed', value: 10, total_count: 100 })
    setModalOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      const payload = {
        ...values,
        start_date: values.start_date?.toISOString(),
        end_date: values.end_date?.toISOString(),
      }
      await couponApi.create(payload)
      message.success('优惠券创建成功')
      setModalOpen(false)
      fetchData()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建失败')
    }
  }

  const handleToggle = async (id: number) => {
    try { await couponApi.toggle(id); fetchData() } catch { message.error('操作失败') }
  }

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除此优惠券？',
      onOk: async () => {
        try { await couponApi.delete(id); message.success('已删除'); fetchData() } catch { message.error('删除失败') }
      },
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name' },
    { title: '券码', dataIndex: 'code', render: (v: string) => <Tag>{v}</Tag> },
    {
      title: '类型', dataIndex: 'coupon_type',
      render: (v: string) => v === 'percent' ? <Tag color="blue">折扣</Tag> : <Tag color="green">满减</Tag>,
    },
    { title: '面值', dataIndex: 'value', render: (v: number, r: any) => r.coupon_type === 'percent' ? `${v}%` : F(v) },
    { title: '门槛', dataIndex: 'min_amount', render: (v: number) => v > 0 ? `满${F(v)}` : '-' },
    { title: '总量', dataIndex: 'total_count' },
    { title: '已用', dataIndex: 'used_count' },
    {
      title: '状态', dataIndex: 'is_active',
      render: (v: boolean) => v ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>,
    },
    {
      title: '操作', key: 'actions', width: 160,
      render: (_: any, r: any) => (
        <Space size="small">
          <Button size="small" icon={r.is_active ? <StopOutlined /> : <CheckCircleOutlined />}
            onClick={() => handleToggle(r.id)}>
            {r.is_active ? '禁用' : '启用'}
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>优惠券管理</h2>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>创建优惠券</Button>
      </div>
      <Table columns={columns} dataSource={coupons} rowKey="id" loading={loading} pagination={{ pageSize: 20 }} />

      <Modal title="创建优惠券" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null} width={500}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="例如：新会员专享" />
          </Form.Item>
          <Form.Item name="code" label="券码（留空自动生成）">
            <Input placeholder="例如：NEW2026" style={{ textTransform: 'uppercase' }} />
          </Form.Item>
          <Form.Item name="coupon_type" label="类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="fixed">满减（固定金额）</Select.Option>
              <Select.Option value="percent">折扣（百分比）</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="value" label="面值" rules={[{ required: true }]}>
            <InputNumber min={0.01} style={{ width: '100%' }} placeholder="满减填金额，折扣填百分比" />
          </Form.Item>
          <Form.Item name="min_amount" label="最低消费（0=无门槛）">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="max_discount" label="最大优惠（折扣类型可用，0=不限）">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="total_count" label="发行量" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Space style={{ width: '100%' }}>
            <Form.Item name="start_date" label="生效时间">
              <DatePicker showTime style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="end_date" label="过期时间">
              <DatePicker showTime style={{ width: 200 }} />
            </Form.Item>
          </Space>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Coupons
