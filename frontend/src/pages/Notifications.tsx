import { useEffect, useState } from 'react'
import { Card, Table, Tag, Button, Space, Select, Popconfirm, message } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import { notificationApi } from '../api'
import type { AppNotification } from '../api/types'

const TYPE_MAP: Record<string, { label: string; color: string }> = {
  system: { label: '系统通知', color: 'default' },
  class_reminder: { label: '上课提醒', color: 'blue' },
  card_expiring: { label: '卡即将到期', color: 'orange' },
  card_expired: { label: '卡已过期', color: 'red' },
  booking_confirm: { label: '预约确认', color: 'green' },
  booking_cancel: { label: '预约取消', color: 'volcano' },
  payment_success: { label: '支付成功', color: 'cyan' },
  marketing: { label: '营销推送', color: 'purple' },
}

const Notifications = () => {
  const [data, setData] = useState<AppNotification[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined)
  const [filterType, setFilterType] = useState<string | undefined>(undefined)

  const fetch = async (p = 1) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { skip: (p - 1) * 20, limit: 20 }
      if (filterRead !== undefined) params.is_read = filterRead
      if (filterType) params.notification_type = filterType
      const res = await notificationApi.getList(params as any)
      setData(res.data)
      setTotal(res.total)
      setPage(p)
    } catch { message.error('获取通知失败') }
    setLoading(false)
  }

  useEffect(() => { fetch() }, [filterRead, filterType])

  const handleMarkRead = async (id: number) => {
    try {
      await notificationApi.markRead(id)
      fetch(page)
    } catch { message.error('操作失败') }
  }

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllRead()
      message.success('全部标记已读')
      fetch(page)
    } catch { message.error('操作失败') }
  }

  const handleDelete = async (id: number) => {
    try {
      await notificationApi.delete(id)
      fetch(page)
    } catch { message.error('删除失败') }
  }

  const columns = [
    { title: '类型', dataIndex: 'notification_type', key: 'type', width: 120, render: (v: string) => {
      const info = TYPE_MAP[v] || { label: v, color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '标题', dataIndex: 'title', key: 'title', render: (v: string, r: AppNotification) => (
      <span style={{ fontWeight: r.is_read ? 'normal' : 'bold' }}>{v}</span>
    )},
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '时间', dataIndex: 'created_at', key: 'time', width: 160, render: (v: string) => new Date(v).toLocaleString() },
    { title: '状态', dataIndex: 'is_read', key: 'status', width: 80, render: (v: boolean) => v ? <Tag>已读</Tag> : <Tag color="processing">未读</Tag> },
    { title: '操作', key: 'action', width: 160, render: (_: unknown, r: AppNotification) => (
      <Space>
        {!r.is_read && <Button type="link" size="small" onClick={() => handleMarkRead(r.id)}>标为已读</Button>}
        <Popconfirm title="确定删除?" onConfirm={() => handleDelete(r.id)}>
          <Button type="link" size="small" danger>删除</Button>
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}><BellOutlined /> 消息通知</h2>
        <Space>
          <Select
            value={filterRead}
            onChange={setFilterRead}
            style={{ width: 120 }}
            allowClear
            placeholder="全部状态"
            options={[{ value: false, label: '未读' }, { value: true, label: '已读' }]}
          />
          <Select
            value={filterType}
            onChange={setFilterType}
            style={{ width: 140 }}
            allowClear
            placeholder="全部类型"
            options={Object.entries(TYPE_MAP).map(([k, v]) => ({ value: k, label: v.label }))}
          />
          <Button onClick={handleMarkAllRead}>全部标为已读</Button>
        </Space>
      </div>

      <Card>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          onRow={(r) => ({
            style: { background: r.is_read ? undefined : '#f6ffed' },
          })}
          pagination={{ current: page, total, pageSize: 20, onChange: fetch }}
        />
      </Card>
    </div>
  )
}

export default Notifications
