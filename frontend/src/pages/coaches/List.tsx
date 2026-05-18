import { useEffect, useState } from 'react';
import { Table, Button, Input, Card, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, TeamOutlined } from '@ant-design/icons';
import { coaches } from '@/services/api';
import { useNavigate } from 'umi';

interface Coach {
  id: number;
  coach_no: string;
  name: string;
  phone: string;
  email?: string;
  specialties: string[];
  hourly_rate: number;
  status: string;
  created_at: string;
}

export default function CoachList() {
  const [data, setData] = useState<Coach[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await coaches.list();
      setData(result);
    } catch (error) {
      message.error('获取教练列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await coaches.delete(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const filteredData = data.filter(
    (item) => item.name.includes(searchText) || item.phone.includes(searchText)
  );

  const columns = [
    {
      title: '教练编号',
      dataIndex: 'coach_no',
      key: 'coach_no',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <TeamOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '专长',
      dataIndex: 'specialties',
      key: 'specialties',
      render: (specialties: string[]) => specialties?.join(', ') || '-',
    },
    { title: '课时费', dataIndex: 'hourly_rate', key: 'hourly_rate', render: (rate: number) => `${rate}元/小时` },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'active' ? (
          <span style={{ color: '#52c41a' }}>在职</span>
        ) : (
          <span style={{ color: '#ff4d4f' }}>离职</span>
        ),
    },
    { title: '入职时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Coach) => (
        <div>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/coaches/${record.id}`)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除该教练吗？"
            onConfirm={() => handleDelete(record.id)}
          >
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
      title="教练列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/coaches/create')}>
          新增教练
        </Button>
      }
    >
      <Input
        placeholder="搜索教练姓名或手机号"
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