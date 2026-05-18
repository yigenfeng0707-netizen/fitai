import { useState } from 'react';
import { Form, Input, Button, Card, Select, message, Row, Col, InputNumber } from 'antd';
import { ArrowLeftOutlined, TeamOutlined } from '@ant-design/icons';
import { coaches } from '@/services/api';
import { useNavigate } from 'umi';

export default function CreateCoach() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { name: string; phone?: string; email?: string; qualifications?: string[]; specialties?: string[]; hourly_rate?: number }) => {
    setLoading(true);
    try {
      await coaches.create(values);
      message.success('教练创建成功');
      navigate('/coaches');
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="新增教练"
      extra={
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/coaches')}>
          返回列表
        </Button>
      }
    >
      <Form form={form} onFinish={onFinish} layout="vertical" size="large">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="name"
              label="姓名"
              rules={[{ required: true, message: '请输入姓名' }]}
            >
              <Input prefix={<TeamOutlined />} placeholder="请输入姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="phone" label="手机号">
              <Input placeholder="请输入手机号" />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="email" label="邮箱">
              <Input placeholder="请输入邮箱" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="hourly_rate" label="课时费(元/小时)">
              <InputNumber placeholder="请输入课时费" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="qualifications" label="资质证书">
              <Select mode="tags" placeholder="请输入资质证书，按回车添加">
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="specialties" label="专长领域">
              <Select mode="tags" placeholder="请输入专长领域，按回车添加">
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建教练
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}