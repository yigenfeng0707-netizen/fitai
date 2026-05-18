import { useState } from 'react';
import { Card, Input, Button, Table, message, Tag } from 'antd';
import { ScanOutlined, SearchOutlined, CheckCircleOutlined } from '@ant-design/icons';

interface CheckinItem {
  id: number;
  member_name: string;
  phone: string;
  course_name: string;
  date: string;
  time: string;
  status: 'checked_in' | 'pending';
}

export default function Checkin() {
  const [searchValue, setSearchValue] = useState('');
  const [data, setData] = useState<CheckinItem[]>([
    { id: 1, member_name: '张三', phone: '138****1234', course_name: '瑜伽基础课', date: '2024-01-15', time: '09:00', status: 'pending' },
    { id: 2, member_name: '李四', phone: '139****5678', course_name: '普拉提核心', date: '2024-01-15', time: '10:30', status: 'pending' },
    { id: 3, member_name: '王五', phone: '137****9012', course_name: '动感单车', date: '2024-01-15', time: '14:00', status: 'checked_in' },
    { id: 4, member_name: '赵六', phone: '136****3456', course_name: '瑜伽进阶', date: '2024-01-15', time: '15:30', status: 'pending' },
    { id: 5, member_name: '钱七', phone: '135****7890', course_name: '私教课', date: '2024-01-15', time: '19:00', status: 'pending' },
  ]);

  const handleCheckin = (id: number) => {
    setData((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: 'checked_in' as const } : item
      )
    );
    message.success('签到成功');
  };

  const filteredData = data.filter(
    (item) =>
      item.member_name.includes(searchValue) ||
      item.phone.includes(searchValue) ||
      item.course_name.includes(searchValue)
  );

  const columns = [
    { title: '会员姓名', dataIndex: 'member_name', key: 'member_name' },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '课程', dataIndex: 'course_name', key: 'course_name' },
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '时间', dataIndex: 'time', key: 'time' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'checked_in' ? (
          <Tag color="green">已签到</Tag>
        ) : (
          <Tag color="orange">待签到</Tag>
        ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: CheckinItem) =>
        record.status === 'pending' ? (
          <Button type="primary" icon={<CheckCircleOutlined />} onClick={() => handleCheckin(record.id)}>
            签到
          </Button>
        ) : (
          <span style={{ color: '#52c41a' }}>已签到</span>
        ),
    },
  ];

  return (
    <Card
      title="签到管理"
      extra={
        <Button type="primary" icon={<ScanOutlined />}>
          扫码签到
        </Button>
      }
    >
      <Input
        placeholder="搜索会员姓名、手机号或课程"
        prefix={<SearchOutlined />}
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table
        dataSource={filteredData}
        columns={columns}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
}