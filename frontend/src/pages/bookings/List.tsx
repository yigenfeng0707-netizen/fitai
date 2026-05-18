import { useEffect, useState } from 'react';
import { Table, Button, Card, Input, message } from 'antd';
import { SearchOutlined, CalendarOutlined, UserOutlined } from '@ant-design/icons';
import { bookings } from '@/services/api';

interface Booking {
  id: number;
  schedule_id: number;
  member_id: number;
  member_name: string;
  course_name: string;
  date: string;
  start_time: string;
  status: string;
  booked_at: string;
}

export default function BookingList() {
  const [data, setData] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await bookings.list();
      const enrichedData = result.map((item: any) => ({
        ...item,
        member_name: '会员' + item.member_id,
        course_name: '课程' + item.schedule_id,
        date: '2024-01-01',
        start_time: '09:00',
      }));
      setData(enrichedData);
    } catch (error) {
      message.error('获取预约列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredData = data.filter(
    (item) => item.member_name.includes(searchText) || item.course_name.includes(searchText)
  );

  const columns = [
    {
      title: '会员',
      dataIndex: 'member_name',
      key: 'member_name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <UserOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    {
      title: '课程',
      dataIndex: 'course_name',
      key: 'course_name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <CalendarOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '时间', dataIndex: 'start_time', key: 'start_time' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          pending: { text: '待确认', color: '#faad14' },
          confirmed: { text: '已确认', color: '#52c41a' },
          canceled: { text: '已取消', color: '#ff4d4f' },
          completed: { text: '已完成', color: '#1890ff' },
        };
        const statusInfo = statusMap[status] || { text: status, color: '#999' };
        return <span style={{ color: statusInfo.color }}>{statusInfo.text}</span>;
      },
    },
    { title: '预约时间', dataIndex: 'booked_at', key: 'booked_at' },
  ];

  return (
    <Card title="预约列表">
      <Input
        placeholder="搜索会员或课程"
        prefix={<SearchOutlined />}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 16, width: 300 }}
      />
      <Table
        dataSource={filteredData}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
}