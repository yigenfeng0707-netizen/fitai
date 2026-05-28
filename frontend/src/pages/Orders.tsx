import { Table, Button, Space, Tag, Select, message, Popconfirm, Modal, Radio, QRCode } from 'antd'
import { DollarOutlined, CloseCircleOutlined, RollbackOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { orderApi } from '../api'
import type { Order } from '../api/types'

const paymentStatusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'orange', text: '待支付' },
  paid: { color: 'green', text: '已支付' },
  refunded: { color: 'red', text: '已退款' },
  cancelled: { color: 'default', text: '已取消' },
}

const paymentMethodMap: Record<string, string> = {
  alipay: '支付宝',
  wechat: '微信支付',
  cash: '现金',
  card: '刷卡',
  transfer: '转账',
}

const Orders = () => {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [payModalOpen, setPayModalOpen] = useState(false)
  const [payingOrderId, setPayingOrderId] = useState<number | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<string>('alipay')
  const [qrcodeUrl, setQrcodeUrl] = useState<string | null>(null)
  const [qrcodeModalOpen, setQrcodeModalOpen] = useState(false)
  const [pollingInterval, setPollingInterval] = useState<ReturnType<typeof setInterval> | null>(null)

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (statusFilter) params.payment_status = statusFilter
      const res = await orderApi.getList(params)
      setOrders(res.data)
    } catch {
      message.error('获取订单列表失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchOrders()
  }, [statusFilter])

  const handlePayClick = (id: number) => {
    setPayingOrderId(id)
    setPaymentMethod('alipay')
    setPayModalOpen(true)
  }

  const startPolling = (orderId: number) => {
    if (pollingInterval) clearInterval(pollingInterval)
    const interval = setInterval(async () => {
      try {
        const order = await orderApi.get(orderId)
        if (order.payment_status === 'paid') {
          clearInterval(interval)
          setPollingInterval(null)
          setQrcodeModalOpen(false)
          message.success('支付成功')
          fetchOrders()
          navigate(`/orders/${orderId}/result?status=success&trade_no=${order.transaction_id || ''}`)
        }
      } catch { /* ignore */ }
    }, 3000)
    setPollingInterval(interval)
  }

  const handlePayConfirm = async () => {
    if (!payingOrderId) return
    try {
      const res = await orderApi.pay(payingOrderId, paymentMethod)
      setPayModalOpen(false)
      if (res.success) {
        if (paymentMethod === 'wechat' && res.data?.code_url) {
          setQrcodeUrl(res.data.code_url)
          setQrcodeModalOpen(true)
          startPolling(payingOrderId)
        } else {
          const tradeNo = res.data?.trade_no || ''
          navigate(`/orders/${payingOrderId}/result?status=success&trade_no=${tradeNo}`)
        }
      } else {
        navigate(`/orders/${payingOrderId}/result?status=fail`)
      }
    } catch {
      message.error('支付失败')
      setPayModalOpen(false)
    }
  }

  const handleQrcodeClose = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
    setQrcodeModalOpen(false)
    setQrcodeUrl(null)
  }

  const handleCancel = async (id: number) => {
    try {
      await orderApi.cancel(id)
      message.success('已取消')
      fetchOrders()
    } catch {
      message.error('取消失败')
    }
  }

  const handleRefund = async (id: number) => {
    try {
      await orderApi.refund(id)
      message.success('已退款')
      fetchOrders()
    } catch {
      message.error('退款失败')
    }
  }

  const columns = [
    { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 200 },
    { title: '会员ID', dataIndex: 'member_id', key: 'member_id', width: 80 },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => `¥${(v ?? 0).toFixed(2)}` },
    { title: '实付', dataIndex: 'actual_amount', key: 'actual_amount', render: (v: number) => `¥${(v ?? 0).toFixed(2)}` },
    {
      title: '支付方式',
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (v?: string) => v ? (paymentMethodMap[v] || v) : '-',
    },
    {
      title: '状态',
      dataIndex: 'payment_status',
      key: 'payment_status',
      render: (v: string) => {
        const m = paymentStatusMap[v]
        return m ? <Tag color={m.color}>{m.text}</Tag> : v
      },
    },
    { title: '备注', dataIndex: 'subject', key: 'subject', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: Order) => (
        <Space>
          {record.payment_status === 'pending' && (
            <>
              <Button type="primary" size="small" icon={<DollarOutlined />} onClick={() => handlePayClick(record.id)}>
                支付
              </Button>
              <Popconfirm title="确定取消?" onConfirm={() => handleCancel(record.id)}>
                <Button size="small" icon={<CloseCircleOutlined />}>取消</Button>
              </Popconfirm>
            </>
          )}
          {record.payment_status === 'paid' && (
            <Popconfirm title="确定退款?" onConfirm={() => handleRefund(record.id)}>
              <Button size="small" icon={<RollbackOutlined />}>退款</Button>
            </Popconfirm>
          )}
          {record.payment_status !== 'pending' && (
            <Button size="small" onClick={() => navigate(`/orders/${record.id}/result?status=${record.payment_status}`)}>
              详情
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 16 }}>订单管理</h1>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <span>状态筛选:</span>
          <Select
            allowClear
            placeholder="全部"
            style={{ width: 140 }}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
            options={[
              { value: 'pending', label: '待支付' },
              { value: 'paid', label: '已支付' },
              { value: 'refunded', label: '已退款' },
              { value: 'cancelled', label: '已取消' },
            ]}
          />
        </Space>
      </div>
      <Table columns={columns} dataSource={orders} rowKey="id" loading={loading} pagination={{ pageSize: 20, showSizeChanger: true }} />

      <Modal
        title="选择支付方式"
        open={payModalOpen}
        onCancel={() => setPayModalOpen(false)}
        onOk={handlePayConfirm}
        okText="确认支付"
      >
        <Radio.Group value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
          <Space direction="vertical">
            <Radio value="alipay">支付宝</Radio>
            <Radio value="wechat">微信支付</Radio>
          </Space>
        </Radio.Group>
      </Modal>

      <Modal
        title="微信支付"
        open={qrcodeModalOpen}
        onCancel={handleQrcodeClose}
        footer={[
          <Button key="close" onClick={handleQrcodeClose}>
            关闭
          </Button>,
          <Button key="done" type="primary" onClick={() => {
            if (pollingInterval) clearInterval(pollingInterval)
            setPollingInterval(null)
            setQrcodeModalOpen(false)
            setQrcodeUrl(null)
            fetchOrders()
            if (payingOrderId) navigate(`/orders/${payingOrderId}/result?status=success`)
          }}>
            已完成支付
          </Button>,
        ]}
      >
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          {qrcodeUrl && <QRCode value={qrcodeUrl} size={256} />}
          <p style={{ marginTop: 16, color: '#666' }}>请使用微信扫描二维码完成支付</p>
        </div>
      </Modal>
    </div>
  )
}

export default Orders
