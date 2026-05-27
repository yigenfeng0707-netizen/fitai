import { useEffect, useState } from 'react'
import { Card, Descriptions, Form, Input, Button, Table, Tag, Modal, Select, Space, message, Tabs } from 'antd'
import { SettingOutlined, UserOutlined } from '@ant-design/icons'
import { settingsApi } from '../api'
import type { OrganizationInfo, UserManageInfo, RoleInfo } from '../api/types'

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  super_admin: { label: '超级管理员', color: 'red' },
  store_owner: { label: '老板/店长', color: 'orange' },
  coach: { label: '教练', color: 'blue' },
  receptionist: { label: '前台', color: 'green' },
  finance: { label: '财务', color: 'cyan' },
}

const Settings = () => {
  const [org, setOrg] = useState<OrganizationInfo | null>(null)
  const [users, setUsers] = useState<UserManageInfo[]>([])
  const [usersTotal, setUsersTotal] = useState(0)
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [orgForm] = Form.useForm()
  const [userForm] = Form.useForm()
  const [editOrgOpen, setEditOrgOpen] = useState(false)
  const [addUserOpen, setAddUserOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchOrg = async () => {
    try { setOrg(await settingsApi.getOrganization()) } catch { message.error('获取组织信息失败') }
    setLoading(false)
  }

  const fetchUsers = async () => {
    try {
      const res = await settingsApi.listUsers({ limit: 100 })
      setUsers(res.data)
      setUsersTotal(res.total)
    } catch { message.error('获取用户列表失败') }
  }

  const fetchRoles = async () => {
    try { setRoles(await settingsApi.listRoles()) } catch { /* ignore */ }
  }

  useEffect(() => { fetchOrg(); fetchUsers(); fetchRoles() }, [])

  const handleUpdateOrg = async () => {
    try {
      const values = await orgForm.validateFields()
      await settingsApi.updateOrganization(values)
      message.success('保存成功')
      setEditOrgOpen(false)
      fetchOrg()
    } catch { message.error('保存失败') }
  }

  const handleAddUser = async () => {
    try {
      const values = await userForm.validateFields()
      await settingsApi.createUser(values)
      message.success('用户创建成功')
      setAddUserOpen(false)
      userForm.resetFields()
      fetchUsers()
    } catch { message.error('创建失败') }
  }

  const handleToggleActive = async (user: UserManageInfo) => {
    try {
      await settingsApi.updateUser(user.id, { is_active: !user.is_active })
      message.success(user.is_active ? '已禁用' : '已启用')
      fetchUsers()
    } catch { message.error('操作失败') }
  }

  const userColumns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '角色', dataIndex: 'role', key: 'role', render: (v: string) => {
      const info = ROLE_LABELS[v] || { label: v, color: 'default' }
      return <Tag color={info.color}>{info.label}</Tag>
    }},
    { title: '状态', dataIndex: 'is_active', key: 'active', render: (v: boolean) => v ? <Tag color="green">正常</Tag> : <Tag color="red">禁用</Tag> },
    { title: '超级管理员', dataIndex: 'is_superuser', key: 'super', render: (v: boolean) => v ? <Tag color="gold">是</Tag> : '-' },
    { title: '最后登录', dataIndex: 'last_login_at', key: 'last', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created', render: (v: string) => new Date(v).toLocaleDateString() },
    { title: '操作', key: 'action', render: (_: unknown, r: UserManageInfo) => (
      <Button type="link" size="small" danger={r.is_active} onClick={() => handleToggleActive(r)}>
        {r.is_active ? '禁用' : '启用'}
      </Button>
    )},
  ]

  if (!org) return <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>{loading ? '加载中...' : '无数据'}</div>

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}><SettingOutlined /> 系统设置</h2>

      <Tabs items={[
        {
          key: 'org',
          label: '门店信息',
          children: (
            <Card>
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="门店名称">{org.name}</Descriptions.Item>
                <Descriptions.Item label="Slug">{org.slug}</Descriptions.Item>
                <Descriptions.Item label="套餐">
                  <Tag color="blue">{org.plan}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={org.status === 'active' ? 'green' : 'red'}>{org.status}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="联系人">{org.contact_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="联系电话">{org.contact_phone || '-'}</Descriptions.Item>
                <Descriptions.Item label="联系邮箱">{org.contact_email || '-'}</Descriptions.Item>
                <Descriptions.Item label="创建时间">{new Date(org.created_at).toLocaleDateString()}</Descriptions.Item>
              </Descriptions>
              <Button type="primary" style={{ marginTop: 16 }} onClick={() => { orgForm.setFieldsValue(org); setEditOrgOpen(true) }}>
                编辑门店信息
              </Button>
            </Card>
          ),
        },
        {
          key: 'users',
          label: '用户管理',
          children: (
            <Card>
              <div style={{ marginBottom: 16 }}>
                <Button type="primary" icon={<UserOutlined />} onClick={() => setAddUserOpen(true)}>新增用户</Button>
                <span style={{ marginLeft: 8, color: '#999' }}>共 {usersTotal} 个用户</span>
              </div>
              <Table dataSource={users} columns={userColumns} rowKey="id" size="small" pagination={false} />
            </Card>
          ),
        },
        {
          key: 'roles',
          label: '角色权限',
          children: (
            <Card>
              <Table
                dataSource={roles}
                columns={[
                  { title: '角色', dataIndex: 'role', key: 'role', render: (v: string) => {
                    const info = ROLE_LABELS[v] || { label: v, color: 'default' }
                    return <Tag color={info.color}>{info.label}</Tag>
                  }},
                  { title: '权限列表', dataIndex: 'permissions', key: 'perms', render: (v: string[]) => (
                    <Space wrap size={[4, 4]}>
                      {v.map(p => <Tag key={p} style={{ fontSize: 11 }}>{p}</Tag>)}
                    </Space>
                  )},
                ]}
                rowKey="role"
                size="small"
                pagination={false}
              />
            </Card>
          ),
        },
      ]} />

      <Modal title="编辑门店信息" open={editOrgOpen} onOk={handleUpdateOrg} onCancel={() => setEditOrgOpen(false)} width={600}>
        <Form form={orgForm} layout="vertical">
          <Form.Item name="name" label="门店名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="contact_name" label="联系人">
            <Input />
          </Form.Item>
          <Form.Item name="contact_phone" label="联系电话">
            <Input />
          </Form.Item>
          <Form.Item name="contact_email" label="联系邮箱">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="新增用户" open={addUserOpen} onOk={handleAddUser} onCancel={() => { setAddUserOpen(false); userForm.resetFields() }}>
        <Form form={userForm} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]} initialValue="receptionist">
            <Select options={Object.entries(ROLE_LABELS).map(([k, v]) => ({ value: k, label: v.label }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Settings
