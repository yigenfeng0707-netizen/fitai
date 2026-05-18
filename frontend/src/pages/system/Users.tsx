import { useState } from 'react';
import { Card, Table, Button, Input, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';

interface User {
  id: number;
  username: string;
  name: string;
  phone: string;
  role: string;
  status: boolean;
}

const roleNames: Record<number, string> = {
  1: '超级管理员',
  2: '店长',
  3: '前台',
  4: '教练',
  5: '财务',
};

export default function Users() {
  const [data, setData] = useState<User[]>([
    { id: 1, username: 'admin', name: '超级管理员', phone: '138****0001', role: '超级管理员', status: true },
    { id: 2, username: 'manager', name: '张经理', phone: '138****0002', role: '店长', status: true },
    { id: 3, username: 'frontdesk', name: '李前台', phone: '138****0003', role: '前台', status: true },
    { id: 4, username: 'coach1', name: '王教练', phone: '138****0004', role: '教练', status: true },
    { id: 5, username: 'finance', name: '陈财务', phone: '138****0005', role: '财务', status: true },
  ]);
  const [searchText, setSearchText] = useState('');

  const handleDelete = (id: number) => {
    setData(data.filter((item) => item.id !== id));
    message.success('删除成功');
  };

  const filteredData = data.filter(
    (item) => item.username.includes(searchText) || item.name.includes(searchText)
  );

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <UserOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: boolean) =>
        status ? <span style={{ color: '#52c41a' }}>启用</span> : <span style={{ color: '#ff4d4f' }}>禁用</span>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: User) => (
        <div>
          <Button type="link" icon={<EditOutlined />}>
            编辑
          </Button>
          <Popconfirm title="确定删除该用户吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ];

  return (
    <Card
      title="用户管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />}>
          新增用户
        </Button>
      }
    >
      <Input
        placeholder="搜索用户名或姓名"
        prefix={<SearchOutlined />}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table dataSource={filteredData} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  );
}