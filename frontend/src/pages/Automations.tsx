import { useEffect, useState } from 'react'
import { Table, Button, Modal, Form, Input, Select, Switch, Tag, Space, Card, Row, Col, Statistic, message, Popconfirm } from 'antd'
import { PlusOutlined, HistoryOutlined, ReloadOutlined } from '@ant-design/icons'
import { automationApi } from '../api/automation'
import type { AutomationRule, AutomationRuleCreate, AutomationRuleUpdate, AutomationLog } from '../api/automation'

const TRIGGER_LABELS: Record<string, string> = {
  member_created: '新会员注册',
  card_expiring: '会员卡即将到期',
  booking_cancelled: '预约取消',
  lead_created: '新潜客创建',
  lead_status_changed: '潜客状态变更',
  member_inactive: '会员长时间未到店',
  birthday: '会员生日',
}

const ACTION_LABELS: Record<string, string> = {
  send_notification: '发送系统通知',
}

const Automations = () => {
  const [rules, setRules] = useState<AutomationRule[]>([])
  const [logs, setLogs] = useState<AutomationLog[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [logModalOpen, setLogModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null)
  const [form] = Form.useForm()
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [logTotal, setLogTotal] = useState(0)

  const fetchRules = async () => {
    setLoading(true)
    try {
      const res = await automationApi.getList({ skip: (page - 1) * 20, limit: 20 })
      setRules(res.data)
      setTotal(res.total)
    } catch {
      message.error('获取自动化规则失败')
    }
    setLoading(false)
  }

  const fetchLogs = async (ruleId?: number) => {
    try {
      const res = await automationApi.getLogs({ rule_id: ruleId, limit: 100 })
      setLogs(res.data)
      setLogTotal(res.total)
    } catch {
      message.error('获取执行日志失败')
    }
  }

  useEffect(() => { fetchRules() }, [page])

  const handleCreate = () => {
    setEditingRule(null)
    form.resetFields()
    form.setFieldsValue({ action_type: 'send_notification' })
    setModalOpen(true)
  }

  const handleEdit = (rule: AutomationRule) => {
    setEditingRule(rule)
    form.setFieldsValue(rule)
    setModalOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      if (editingRule) {
        await automationApi.update(editingRule.id, values as AutomationRuleUpdate)
        message.success('更新成功')
      } else {
        await automationApi.create(values as AutomationRuleCreate)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchRules()
    } catch {
      message.error('操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await automationApi.delete(id)
      message.success('删除成功')
      fetchRules()
    } catch {
      message.error('删除失败')
    }
  }

  const handleToggle = async (id: number) => {
    try {
      await automationApi.toggle(id)
      fetchRules()
    } catch {
      message.error('操作失败')
    }
  }

  const handleShowLogs = (ruleId?: number) => {
    fetchLogs(ruleId)
    setLogModalOpen(true)
  }

  const handleCheckTimeTriggers = async () => {
    try {
      await automationApi.checkTimeTriggers()
      message.success('已检查并执行时间触发规则')
      fetchRules()
    } catch {
      message.error('检查失败')
    }
  }

  const columns = [
    { title: '规则名称', dataIndex: 'name', key: 'name' },
    {
      title: '触发条件', dataIndex: 'trigger_type', key: 'trigger_type',
      render: (v: string) => TRIGGER_LABELS[v] || v,
    },
    {
      title: '执行动作', dataIndex: 'action_type', key: 'action_type',
      render: (v: string) => ACTION_LABELS[v] || v,
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (_: boolean, record: AutomationRule) => (
        <Switch checked={record.is_active} onChange={() => handleToggle(record.id)} size="small" />
      ),
    },
    { title: '执行次数', dataIndex: 'execution_count', key: 'execution_count', width: 100 },
    {
      title: '操作', key: 'action', width: 220,
      render: (_: unknown, record: AutomationRule) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" onClick={() => handleShowLogs(record.id)} icon={<HistoryOutlined />}>日志</Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const activeCount = rules.filter(r => r.is_active).length

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="自动化规则" value={total} suffix="条" /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="已启用" value={activeCount} suffix={`/ ${total}`} valueStyle={{ color: '#52c41a' }} /></Card>
        </Col>
      </Row>

      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建规则</Button>
        <Button icon={<ReloadOutlined />} onClick={handleCheckTimeTriggers}>检查时间触发</Button>
        <Button icon={<HistoryOutlined />} onClick={() => handleShowLogs()}>全部日志</Button>
      </Space>

      <Table
        dataSource={rules}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page, total, pageSize: 20,
          onChange: (p) => setPage(p),
        }}
      />

      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        width={560}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
            <Input placeholder="例: 新会员欢迎通知" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="trigger_type" label="触发条件" rules={[{ required: true }]}>
            <Select>
              {Object.entries(TRIGGER_LABELS).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="trigger_config" label="触发配置 (JSON)">
            <Input.TextArea rows={3} placeholder='{"days_before": 7, "inactive_days": 30}' />
          </Form.Item>
          <Form.Item name="action_type" label="执行动作" rules={[{ required: true }]}>
            <Select>
              {Object.entries(ACTION_LABELS).map(([k, v]) => (
                <Select.Option key={k} value={k}>{v}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="action_config" label="动作配置 (JSON)">
            <Input.TextArea rows={4} placeholder='{"title": "通知标题", "content": "内容模板，支持 {{member_name}} 等变量", "target_users": ["admins"]}' />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="执行日志"
        open={logModalOpen}
        onCancel={() => setLogModalOpen(false)}
        footer={null}
        width={700}
      >
        <Table
          dataSource={logs}
          rowKey="id"
          size="small"
          pagination={{ total: logTotal, pageSize: 10 }}
          columns={[
            { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
            { title: '实体类型', dataIndex: 'trigger_entity_type', key: 'trigger_entity_type' },
            { title: '实体ID', dataIndex: 'trigger_entity_id', key: 'trigger_entity_id' },
            {
              title: '状态', dataIndex: 'status', key: 'status',
              render: (v: string) => v === 'success' ? <Tag color="green">成功</Tag> : <Tag color="red">失败</Tag>,
            },
            { title: '错误', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
          ]}
        />
      </Modal>
    </div>
  )
}

export default Automations
