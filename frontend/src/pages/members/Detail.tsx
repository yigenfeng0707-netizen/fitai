import { useEffect, useState } from 'react';
import { Card, Button, Form, Input, Select, Tabs, Table, message } from 'antd';
import { ArrowLeftOutlined, CreditCardOutlined, FileTextOutlined, UserOutlined } from '@ant-design/icons';
import { members } from '@/services/api';
import { useNavigate, useParams } from 'umi';

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

interface CardItem {
  id: number;
  card_no: string;
  card_type: string;
  total_hours: number;
  used_hours: number;
  balance: number;
  status: string;
}

export default function MemberDetail() {
  const { id } = useParams<{ id: string }>();
  const [member, setMember] = useState<Member | null>(null);
  const [cards, setCards] = useState<CardItem[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [memberData, cardsData] = await Promise.all([
        members.get(parseInt(id || '0')),
        members.cards(parseInt(id || '0')),
      ]);
      setMember(memberData);
      setCards(cardsData);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (!member) return null;

  const cardColumns = [
    { title: '卡号', dataIndex: 'card_no', key: 'card_no' },
    { title: '卡类型', dataIndex: 'card_type', key: 'card_type' },
    { title: '总课时', dataIndex: 'total_hours', key: 'total_hours' },
    { title: '已用课时', dataIndex: 'used_hours', key: 'used_hours' },
    { title: '余额', dataIndex: 'balance', key: 'balance' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) =>
        status === 'active' ? (
          <span style={{ color: '#52c41a' }}>正常</span>
        ) : (
          <span style={{ color: '#ff4d4f' }}>过期</span>
        ),
    },
  ];

  return (
    <Card
      title="会员详情"
      extra={
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/members')}>
          返回列表
        </Button>
      }
    >
      <Tabs defaultActiveKey="info">
        <Tabs.TabPane tab="基本信息" key="info">
          <Form layout="vertical" size="large">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              <Form.Item label="会员编号">
                <Input disabled value={member.member_no} />
              </Form.Item>
              <Form.Item label="姓名">
                <Input disabled value={member.name} prefix={<UserOutlined />} />
              </Form.Item>
              <Form.Item label="手机号">
                <Input disabled value={member.phone} />
              </Form.Item>
              <Form.Item label="邮箱">
                <Input disabled value={member.email || '-'} />
              </Form.Item>
              <Form.Item label="会员等级">
                <Select disabled defaultValue={member.level?.name}>
                  <Select.Option value={member.level?.name}>{member.level?.name}</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item label="积分">
                <Input disabled value={member.points} />
              </Form.Item>
              <Form.Item label="状态">
                <Select disabled defaultValue={member.status}>
                  <Select.Option value="active">正常</Select.Option>
                  <Select.Option value="frozen">冻结</Select.Option>
                  <Select.Option value="cancelled">注销</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item label="创建时间">
                <Input disabled value={member.created_at} />
              </Form.Item>
            </div>
          </Form>
        </Tabs.TabPane>
        <Tabs.TabPane tab="会员卡" key="cards">
          <Button type="primary" icon={<CreditCardOutlined />} style={{ marginBottom: 16 }}>
            办卡
          </Button>
          <Table dataSource={cards} columns={cardColumns} rowKey="id" loading={loading} />
        </Tabs.TabPane>
        <Tabs.TabPane tab="体测记录" key="tests">
          <Button type="primary" icon={<FileTextOutlined />} style={{ marginBottom: 16 }}>
            新增体测
          </Button>
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            暂无体测记录
          </div>
        </Tabs.TabPane>
      </Tabs>
    </Card>
  );
}