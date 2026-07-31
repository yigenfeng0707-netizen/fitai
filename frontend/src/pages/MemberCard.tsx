import { useEffect, useState } from 'react'
import { Card, Descriptions, Tag, Table, Modal, Form, InputNumber, Select, Input, Button, Row, Col, Statistic, message, Space, Alert } from 'antd'
import { CreditCardOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { memberApi, cardApi } from '../api'
import type { Member, CardTransaction } from '../api/types'

const CARD_TYPE_MAP: Record<string, { label: string; color: string }> = {
  single: { label: '次卡', color: 'blue' },
  monthly: { label: '月卡', color: 'green' },
  quarterly: { label: '季卡', color: 'orange' },
  yearly: { label: '年卡', color: 'purple' },
  stored: { label: '储值卡', color: 'cyan' },
}

const TXN_TYPE_MAP: Record<string, { label: string; color: string }> = {
  recharge: { label: '充值', color: 'green' },
  renew: { label: '续费', color: 'blue' },
  upgrade: { label: '升级', color: 'purple' },
  consume: { label: '消费', color: 'orange' },
  refund: { label: '退款', color: 'red' },
  freeze: { label: '冻结', color: 'default' },
  unfreeze: { label: '解冻', color: 'cyan' },
}

const MemberCard = () => {
  const { memberId } = useParams()
  const navigate = useNavigate()
  const [member, setMember] = useState<Member | null>(null)
  const [transactions, setTransactions] = useState<CardTransaction[]>([])
  const [txnTotal, setTxnTotal] = useState(0)
  const [txnPage, setTxnPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [renewOpen, setRenewOpen] = useState(false)
  const [rechargeOpen, setRechargeOpen] = useState(false)
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [renewForm] = Form.useForm()
  const [rechargeForm] = Form.useForm()
  const [upgradeForm] = Form.useForm()

  const fetchMember = async () => {
    if (!memberId) return
    setLoading(true)
    try {
      const data = await memberApi.get(Number(memberId))
      setMember(data)
    } catch { message.error('获取会员信息失败') }
    setLoading(false)
  }

  const fetchTransactions = async (page = 1) => {
    if (!memberId) return
    try {
      const res = await cardApi.getTransactions(Number(memberId), { skip: (page - 1) * 10, limit: 10 })
      setTransactions(res.data)
      setTxnTotal(res.total)
      setTxnPage(page)
    } catch { message.error('获取交易记录失败') }
  }

  useEffect(() => { fetchMember(); fetchTransactions() }, [memberId])

  const handleRenew = async () => {
    try {
      const values = await renewForm.validateFields()
      await cardApi.renew(Number(memberId), values)
      message.success('续费成功')
      setRenewOpen(false)
      renewForm.resetFields()
      fetchMember()
      fetchTransactions()
    } catch { message.error('续费失败') }
  }

  const handleRecharge = async () => {
    try {
      const values = await rechargeForm.validateFields()
      await cardApi.recharge(Number(memberId), values)
      message.success('充值成功')
      setRechargeOpen(false)
      rechargeForm.resetFields()
      fetchMember()
      fetchTransactions()
    } catch { message.error('充值失败') }
  }

  const handleUpgrade = async () => {
    try {
      const values = await upgradeForm.validateFields()
      await cardApi.upgrade(Number(memberId), values)
      message.success('升级成功')
      setUpgradeOpen(false)
      upgradeForm.resetFields()
      fetchMember()
      fetchTransactions()
    } catch { message.error('升级失败') }
  }

  if (!member) return <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>{loading ? '加载中...' : '会员不存在'}</div>

  const cardInfo = CARD_TYPE_MAP[member.card_type || ''] || { label: '未开卡', color: 'default' }
  const isExpired = member.card_end_date ? new Date(member.card_end_date) < new Date() : false
  const daysLeft = member.card_end_date ? Math.ceil((new Date(member.card_end_date).getTime() - Date.now()) / 86400000) : null

  const txnColumns = [
    { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => new Date(v).toLocaleString() },
    { title: '类型', dataIndex: 'transaction_type', key: 'type', render: (v: string) => {
      const info = TXN_TYPE_MAP[v] || { label: v, color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => v > 0 ? `¥${v}` : '-' },
    { title: '次数变动', dataIndex: 'count_change', key: 'count', render: (v: number) => v !== 0 ? (v > 0 ? `+${v}` : `${v}`) : '-' },
    { title: '余额变动', key: 'balance', render: (_: unknown, r: CardTransaction) => r.balance_after !== r.balance_before ? `${r.balance_before} → ${r.balance_after}` : '-' },
    { title: '卡种变动', key: 'card_type', render: (_: unknown, r: CardTransaction) => {
      if (r.card_type_before && r.card_type_after && r.card_type_before !== r.card_type_after) {
        const before = CARD_TYPE_MAP[r.card_type_before]?.label || r.card_type_before
        const after = CARD_TYPE_MAP[r.card_type_after]?.label || r.card_type_after
        return <span>{before} → {after}</span>
      }
      return '-'
    }},
    { title: '说明', dataIndex: 'description', key: 'desc', ellipsis: true },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}><CreditCardOutlined /> {member.name} - 会员卡管理</h2>
        <Button onClick={() => navigate(-1)}>返回</Button>
      </div>

      {isExpired && <Alert message="此会员卡已过期" type="error" showIcon style={{ marginBottom: 16 }} />}
      {!isExpired && daysLeft !== null && daysLeft <= 7 && <Alert message={`会员卡将在 ${daysLeft} 天后到期`} type="warning" showIcon style={{ marginBottom: 16 }} />}

      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic title="卡种" value={cardInfo.label} valueStyle={{ fontSize: 20 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="剩余次数" value={member.card_remaining_count ?? 0} suffix="次" />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="储值余额" value={member.card_balance ?? 0} prefix="¥" precision={2} />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="会员姓名">{member.name}</Descriptions.Item>
          <Descriptions.Item label="手机号">{member.phone}</Descriptions.Item>
          <Descriptions.Item label="卡种">
            <Tag color={cardInfo.color}>{cardInfo.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="会员状态">
            <Tag color={member.status === 'active' ? 'green' : 'red'}>{member.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="开卡日期">{member.card_start_date ? new Date(member.card_start_date).toLocaleDateString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="到期日期">
            {member.card_end_date ? (
              <span style={{ color: isExpired ? 'red' : daysLeft !== null && daysLeft <= 7 ? 'orange' : undefined }}>
                {new Date(member.card_end_date).toLocaleDateString()}
                {isExpired ? ' (已过期)' : daysLeft !== null ? ` (剩${daysLeft}天)` : ''}
              </span>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="累计消费">¥{member.total_consumption}</Descriptions.Item>
          <Descriptions.Item label="会员等级">Lv.{member.level}</Descriptions.Item>
        </Descriptions>
        <Space style={{ marginTop: 16 }}>
          <Button type="primary" onClick={() => setRenewOpen(true)}>续费</Button>
          <Button onClick={() => setRechargeOpen(true)}>充值</Button>
          <Button onClick={() => setUpgradeOpen(true)}>升级卡种</Button>
        </Space>
      </Card>

      <Card title="交易记录" style={{ marginTop: 16 }}>
        <Table
          dataSource={transactions}
          columns={txnColumns}
          rowKey="id"
          size="small"
          pagination={{ current: txnPage, total: txnTotal, pageSize: 10, onChange: fetchTransactions }}
        />
      </Card>

      <Modal title="续费" open={renewOpen} onOk={handleRenew} onCancel={() => { setRenewOpen(false); renewForm.resetFields() }}>
        <Form form={renewForm} layout="vertical">
          <Form.Item name="card_type" label="卡种" rules={[{ required: true }]}>
            <Select options={[{ value: 'monthly', label: '月卡' }, { value: 'quarterly', label: '季卡' }, { value: 'yearly', label: '年卡' }]} />
          </Form.Item>
          <Form.Item name="duration_days" label="续费天数" rules={[{ required: true }]} initialValue={30}>
            <InputNumber min={1} max={3650} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="amount" label="金额" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="description" label="备注">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="充值" open={rechargeOpen} onOk={handleRecharge} onCancel={() => { setRechargeOpen(false); rechargeForm.resetFields() }}>
        <Form form={rechargeForm} layout="vertical">
          <Form.Item name="amount" label="充值金额" rules={[{ required: true }]} initialValue={100}>
            <InputNumber min={0.01} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="count" label="充值次数" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} suffix="次" />
          </Form.Item>
          <Form.Item name="description" label="备注">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="升级卡种" open={upgradeOpen} onOk={handleUpgrade} onCancel={() => { setUpgradeOpen(false); upgradeForm.resetFields() }}>
        <Form form={upgradeForm} layout="vertical">
          <Form.Item name="new_card_type" label="新卡种" rules={[{ required: true }]}>
            <Select options={[{ value: 'single', label: '次卡' }, { value: 'monthly', label: '月卡' }, { value: 'quarterly', label: '季卡' }, { value: 'yearly', label: '年卡' }, { value: 'stored', label: '储值卡' }]} />
          </Form.Item>
          <Form.Item name="amount" label="补差金额" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="description" label="备注">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MemberCard
