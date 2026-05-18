import { useEffect, useState } from 'react';
import { Table, Button, Input, Card, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons';
import { members } from '@/services/api';
import { useNavigate } from 'umi';

interface Member {
  id: number;
  member_no: string;
  name: string;
  phone: string;
  email?: string;
  level: { name: string };
  points: number;
  status: string;
  created_at: string;
}

export default function MemberList() {
  const [data, setData] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await members.list();
      setData(result);
    } catch (error) {
      message.error('获取会员列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await members.delete(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const filteredData = data.filter(
    (item) =>
      item.name.includes(searchText) ||
      item.phone.includes(searchText) ||
      item.member_no.includes(searchText)
  );

  const columns = [
    { title: '会员编号', dataIndex: 'member_no', key: 'member_no' },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <UserOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    { title: '手机号', dataIndex: 'phone', key: 'phone' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '会员等级',
      dataIndex: 'level',
      key: 'level',
      render: (level: { name: string }) => level?.name || '-',
    },
    { title: '积分', dataIndex: 'points', key: 'points' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'active' ? (
          <span style={{ color: '#52c41a' }}>正常</span>
        ) : status === 'frozen' ? (
          <span style={{ color: '#faad14' }}>冻结</span>
        ) : (
          <span style={{ color: '#ff4d4f' }}>注销</span>
        ),
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Member) => (
        <div>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/members/${record.id}`)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除该会员吗？"
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
      title="会员列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/members/create')}>
          新增会员
        </Button>
      }
    >
      <Input
        placeholder="搜索姓名、手机号或会员编号"
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