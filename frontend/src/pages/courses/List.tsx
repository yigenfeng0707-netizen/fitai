import { useEffect, useState } from 'react';
import { Table, Button, Input, Card, Popconfirm, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { courses } from '@/services/api';
import { useNavigate } from 'umi';

interface Course {
  id: number;
  name: string;
  category: { name: string };
  course_type: string;
  duration: number;
  price: number;
  max_capacity: number;
  is_active: boolean;
  created_at: string;
}

export default function CourseList() {
  const [data, setData] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await courses.list();
      setData(result);
    } catch (error) {
      message.error('获取课程列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await courses.delete(id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const filteredData = data.filter(
    (item) => item.name.includes(searchText) || item.category?.name.includes(searchText)
  );

  const columns = [
    {
      title: '课程名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <ClockCircleOutlined style={{ marginRight: 8 }} />
          {text}
        </span>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: { name: string }) => category?.name || '-',
    },
    {
      title: '类型',
      dataIndex: 'course_type',
      key: 'course_type',
      render: (type: string) =>
        type === 'group' ? '团课' : type === 'private' ? '私教' : type,
    },
    { title: '时长(分钟)', dataIndex: 'duration', key: 'duration' },
    { title: '价格(元)', dataIndex: 'price', key: 'price' },
    { title: '最大人数', dataIndex: 'max_capacity', key: 'max_capacity' },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) =>
        active ? <span style={{ color: '#52c41a' }}>启用</span> : <span style={{ color: '#ff4d4f' }}>停用</span>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Course) => (
        <div>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/courses/${record.id}`)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除该课程吗？"
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
      title="课程列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/courses/create')}>
          新增课程
        </Button>
      }
    >
      <Input
        placeholder="搜索课程名称或分类"
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