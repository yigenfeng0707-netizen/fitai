import { useEffect, useState } from 'react'
import { Card, Table, Tag, Select, Button, message } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { cardApi } from '../api'
import type { ExpiringCard, Member } from '../api/types'

const CARD_TYPE_MAP: Record<string, { label: string; color: string }> = {
  single: { label: '次卡', color: 'blue' },
  monthly: { label: '月卡', color: 'green' },
  quarterly: { label: '季卡', color: 'orange' },
  yearly: { label: '年卡', color: 'purple' },
  stored: { label: '储值卡', color: 'cyan' },
}

const Cards = () => {
  const navigate = useNavigate()
  const [tab, setTab] = useState<'expiring' | 'expired'>('expiring')
  const [expiring, setExpiring] = useState<ExpiringCard[]>([])
  const [expired, setExpired] = useState<Member[]>([])
  const [expiredTotal, setExpiredTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)

  const fetchExpiring = async () => {
    setLoading(true)
    try {
      const data = await cardApi.getExpiring(days)
      setExpiring(data)
    } catch { message.error('获取到期提醒失败') }
    setLoading(false)
  }

  const fetchExpired = async (page = 1) => {
    setLoading(true)
    try {
      const res = await cardApi.getExpired({ skip: (page - 1) * 20, limit: 20 })
      setExpired(res.data)
      setExpiredTotal(res.total)
    } catch { message.error('获取过期会员失败') }
    setLoading(false)
  }

  useEffect(() => { if (tab === 'expiring') fetchExpiring(); else fetchExpired() }, [tab, days])

  const expiringColumns = [
    { title: '会员姓名', dataIndex: 'member_name', key: 'name' },
    { title: '手机号', dataIndex: 'member_phone', key: 'phone' },
    { title: '卡种', dataIndex: 'card_type', key: 'card_type', render: (v: string) => {
      const info = CARD_TYPE_MAP[v] || { label: v || '未知', color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '到期日期', dataIndex: 'card_end_date', key: 'end', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '剩余天数', dataIndex: 'days_remaining', key: 'days', render: (v: number) => (
      <span style={{ color: v <= 3 ? 'red' : v <= 7 ? 'orange' : undefined, fontWeight: 'bold' }}>
        {v} 天
      </span>
    )},
    { title: '操作', key: 'action', render: (_: unknown, r: ExpiringCard) => (
      <Button type="link" size="small" onClick={() => navigate(`/member-card/${r.member_id}`)}>管理</Button>
    )},
  ]

  const expiredColumns = [
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '卡种', dataIndex: 'card_type', key: 'card_type', render: (v: string) => {
      const info = CARD_TYPE_MAP[v] || { label: v || '未知', color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '到期日期', dataIndex: 'card_end_date', key: 'end', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '操作', key: 'action', render: (_: unknown, r: Member) => (
      <Button type="link" size="small" onClick={() => navigate(`/member-card/${r.id}`)}>管理</Button>
    )},
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}><WarningOutlined /> 会员卡管理</h1>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <Button type={tab === 'expiring' ? 'primary' : 'default'} onClick={() => setTab('expiring')} style={{ marginRight: 8 }}>
              即将到期
            </Button>
            <Button type={tab === 'expired' ? 'primary' : 'default'} onClick={() => setTab('expired')}>
              已过期
            </Button>
          </div>
          {tab === 'expiring' && (
            <Select value={days} onChange={setDays} style={{ width: 160 }} options={[
              { value: 3, label: '3天内到期' },
              { value: 7, label: '7天内到期' },
              { value: 15, label: '15天内到期' },
              { value: 30, label: '30天内到期' },
            ]} />
          )}
        </div>

        {tab === 'expiring' ? (
          <Table dataSource={expiring} columns={expiringColumns} rowKey="member_id" loading={loading} size="small" />
        ) : (
          <Table dataSource={expired} columns={expiredColumns} rowKey="id" loading={loading} size="small" pagination={{ total: expiredTotal, pageSize: 20, onChange: fetchExpired }} />
        )}
      </Card>
    </div>
  )
}

export default Cards
