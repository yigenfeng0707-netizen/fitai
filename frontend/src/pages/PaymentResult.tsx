import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Result, Button, Spin, Descriptions, Tag } from 'antd'
import { orderApi } from '../api'
import type { Order } from '../api/types'

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'orange', text: '待支付' },
  paid: { color: 'green', text: '已支付' },
  refunded: { color: 'red', text: '已退款' },
  cancelled: { color: 'default', text: '已取消' },
}

const PaymentResult = () => {
  const { orderId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  const status = searchParams.get('status')

  useEffect(() => {
    if (!orderId) return
    orderApi.get(Number(orderId))
      .then((res) => setOrder(res))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [orderId])

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />
  }

  if (status === 'success' || status === 'paid') {
    return (
      <Result
        status="success"
        title="支付成功"
        subTitle={order ? `订单 ${order.order_no} 已支付成功` : undefined}
        extra={[
          <Button type="primary" key="orders" onClick={() => navigate('/orders')}>
            返回订单列表
          </Button>,
          <Button key="dashboard" onClick={() => navigate('/dashboard')}>
            返回工作台
          </Button>,
        ]}
      >
        {order && (
          <Descriptions column={2} bordered size="small" style={{ maxWidth: 600, margin: '0 auto' }}>
            <Descriptions.Item label="订单号">{order.order_no}</Descriptions.Item>
            <Descriptions.Item label="金额">¥{order.actual_amount.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="支付方式">{order.payment_method || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusMap[order.payment_status]?.color}>{statusMap[order.payment_status]?.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="支付时间">{order.paid_at || '-'}</Descriptions.Item>
            <Descriptions.Item label="交易号">{order.transaction_id || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Result>
    )
  }

  if (status === 'fail' || status === 'cancelled') {
    return (
      <Result
        status="error"
        title="支付失败"
        subTitle="支付未完成，请重试或联系管理员"
        extra={[
          <Button type="primary" key="retry" onClick={() => navigate('/orders')}>
            重新支付
          </Button>,
          <Button key="dashboard" onClick={() => navigate('/dashboard')}>
            返回工作台
          </Button>,
        ]}
      />
    )
  }

  return (
    <Result
      status="info"
      title="订单详情"
      extra={[
        <Button type="primary" key="orders" onClick={() => navigate('/orders')}>
          返回订单列表
        </Button>,
      ]}
    >
      {order && (
        <Descriptions column={2} bordered size="small" style={{ maxWidth: 600, margin: '0 auto' }}>
          <Descriptions.Item label="订单号">{order.order_no}</Descriptions.Item>
          <Descriptions.Item label="金额">¥{order.actual_amount.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="支付方式">{order.payment_method || '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[order.payment_status]?.color}>{statusMap[order.payment_status]?.text}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{order.created_at || '-'}</Descriptions.Item>
          <Descriptions.Item label="交易号">{order.transaction_id || '-'}</Descriptions.Item>
        </Descriptions>
      )}
    </Result>
  )
}

export default PaymentResult
