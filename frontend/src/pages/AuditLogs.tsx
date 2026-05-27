import { useEffect, useState } from 'react'
import { Card, Table, Tag, Select, Space } from 'antd'
import { HistoryOutlined } from '@ant-design/icons'
import { auditApi } from '../api'
import type { AuditLog } from '../api/types'

const ACTION_MAP: Record<string, { label: string; color: string }> = {
  create: { label: '创建', color: 'green' },
  update: { label: '更新', color: 'blue' },
  delete: { label: '删除', color: 'red' },
  pay: { label: '支付', color: 'cyan' },
  cancel: { label: '取消', color: 'orange' },
  card_renew: { label: '续费', color: 'purple' },
  card_recharge: { label: '充值', color: 'geekblue' },
  card_upgrade: { label: '升级', color: 'magenta' },
  checkin: { label: '签到', color: 'lime' },
}

const RESOURCE_MAP: Record<string, string> = {
  member: '会员',
  coach: '教练',
  course: '课程',
  order: '订单',
  booking: '预约',
  schedule: '排课',
  lead: '潜客',
}

const AuditLogs = () => {
  const [data, setData] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState<string | undefined>(undefined)
  const [resourceFilter, setResourceFilter] = useState<string | undefined>(undefined)

  const fetch = async (p = 1) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { skip: (p - 1) * 20, limit: 20 }
      if (actionFilter) params.action = actionFilter
      if (resourceFilter) params.resource = resourceFilter
      const res = await auditApi.getList(params as any)
      setData(res.data)
      setTotal(res.total)
      setPage(p)
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { fetch() }, [actionFilter, resourceFilter])

  const columns = [
    { title: '时间', dataIndex: 'created_at', key: 'time', width: 160, render: (v: string) => new Date(v).toLocaleString() },
    { title: '操作', dataIndex: 'action', key: 'action', width: 100, render: (v: string) => {
      const info = ACTION_MAP[v] || { label: v, color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '资源', dataIndex: 'resource', key: 'resource', width: 80, render: (v: string) => RESOURCE_MAP[v] || v || '-' },
    { title: '资源ID', dataIndex: 'resource_id', key: 'rid', width: 80 },
    { title: '说明', dataIndex: 'detail', key: 'detail', ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip', width: 120, render: (v: string) => v || '-' },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}><HistoryOutlined /> 操作日志</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Select
            value={actionFilter}
            onChange={setActionFilter}
            style={{ width: 120 }}
            allowClear
            placeholder="操作类型"
            options={Object.entries(ACTION_MAP).map(([k, v]) => ({ value: k, label: v.label }))}
          />
          <Select
            value={resourceFilter}
            onChange={setResourceFilter}
            style={{ width: 120 }}
            allowClear
            placeholder="资源类型"
            options={Object.entries(RESOURCE_MAP).map(([k, v]) => ({ value: k, label: v }))}
          />
        </Space>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{ current: page, total, pageSize: 20, onChange: fetch }}
        />
      </Card>
    </div>
  )
}

export default AuditLogs
