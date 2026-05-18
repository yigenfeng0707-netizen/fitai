import { useState } from 'react';
import { Card, Table, Button, Input, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, ShieldOutlined } from '@ant-design/icons';

interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string;
}

export default function Roles() {
  const [data, setData] = useState<Role[]>([
    { id: 1, name: '超级管理员', description: '系统最高权限', permissions: '全部权限' },
    { id: 2, name: '店长', description: '门店管理权限', permissions: '会员、课程、预约、教练、财务' },
    { id: 3, name: '前台', description: '前台接待权限', permissions: '会员、预约' },
    { id: 4, name: '教练', description: '教学管理权限', permissions: '预约、学员管理' },
    { id: 5, name: '财务', description: '财务管理权限', permissions: '财务报表、订单' },
  ]);
  const [searchText, setSearchText] = useState('');

  const handleDelete = (id: number) => {
    setData(data.filter((item) => item.id !== id));
    message.success('删除成功');
  };

  const filteredData = data.filter((item) => item.name.includes(searchText));

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <ShieldOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    { title: '描述', dataIndex: 'description', key: 'description' },
    { title: '权限', dataIndex: 'permissions', key: 'permissions' },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Role) => (
        <div>
          <Button type="link" icon={<EditOutlined />}>
            编辑权限
          </Button>
          <Popconfirm title="确定删除该角色吗？" onConfirm={() => handleDelete(record.id)}>
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
      title="角色管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />}>
          新增角色
        </Button>
      }
    >
      <Input
        placeholder="搜索角色名称"
        prefix={<SearchOutlined />}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table dataSource={filteredData} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  );
}