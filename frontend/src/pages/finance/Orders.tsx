import { useState } from 'react';
import { Card, Input, Table, Button, Select, Tag } from 'antd';
import { SearchOutlined, WalletOutlined } from '@ant-design/icons';

interface Order {
  id: number;
  order_no: string;
  member_name: string;
  phone: string;
  type: string;
  amount: number;
  status: string;
  created_at: string;
}

export default function Orders() {
  const [searchValue, setSearchValue] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const data: Order[] = [
    { id: 1, order_no: 'ORD20240115001', member_name: '张三', phone: '138****1234', type: '会员卡充值', amount: 2000, status: 'completed', created_at: '2024-01-15 09:30' },
    { id: 2, order_no: 'ORD20240115002', member_name: '李四', phone: '139****5678', type: '课程购买', amount: 580, status: 'completed', created_at: '2024-01-15 10:15' },
    { id: 3, order_no: 'ORD20240115003', member_name: '王五', phone: '137****9012', type: '私教课', amount: 1200, status: 'pending', created_at: '2024-01-15 14:20' },
    { id: 4, order_no: 'ORD20240115004', member_name: '赵六', phone: '136****3456', type: '次卡购买', amount: 880, status: 'completed', created_at: '2024-01-15 15:45' },
    { id: 5, order_no: 'ORD20240115005', member_name: '钱七', phone: '135****7890', type: '会员卡升级', amount: 3000, status: 'refund', created_at: '2024-01-15 16:30' },
  ];

  const filteredData = data.filter((item) => {
    const matchesSearch = item.order_no.includes(searchValue) || item.member_name.includes(searchValue) || item.phone.includes(searchValue);
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const columns = [
    { title: '订单编号', dataIndex: 'order_no', key: 'order_no' },
    { title: '会员', dataIndex: 'member_name', key: 'member_name' },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <span style={{ color: '#52c41a', fontWeight: 'bold' }}>{amount}元</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          completed: { text: '已完成', color: 'green' },
          pending: { text: '待支付', color: 'orange' },
          refund: { text: '已退款', color: 'red' },
        };
        const statusInfo = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
      },
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: () => <Button type="link">详情</Button>,
    },
  ];

  return (
    <Card title="订单管理">
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <Input
          placeholder="搜索订单号、会员姓名或手机号"
          prefix={<SearchOutlined />}
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          style={{ width: 300 }}
        />
        <Select
          placeholder="状态筛选"
          value={statusFilter}
          onChange={(value) => setStatusFilter(value)}
          style={{ width: 150 }}
        >
          <Select.Option value="all">全部</Select.Option>
          <Select.Option value="completed">已完成</Select.Option>
          <Select.Option value="pending">待支付</Select.Option>
          <Select.Option value="refund">已退款</Select.Option>
        </Select>
      </div>
      <Table dataSource={filteredData} columns={columns} rowKey="id" pagination={{ pageSize: 10 }} />
    </Card>
  );
}