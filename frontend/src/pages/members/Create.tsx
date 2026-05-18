import { useState } from 'react';
import { Form, Input, Button, Card, Select, message, Row, Col } from 'antd';
import { ArrowLeftOutlined, UserOutlined } from '@ant-design/icons';
import { members } from '@/services/api';
import { useNavigate } from 'umi';

export default function CreateMember() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { name: string; phone: string; email?: string; level_id?: number }) => {
    setLoading(true);
    try {
      await members.create(values);
      message.success('会员创建成功');
      navigate('/members');
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="新增会员"
      extra={
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/members')}>
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
              <Input prefix={<UserOutlined />} placeholder="请输入姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="phone"
              label="手机号"
              rules={[{ required: true, message: '请输入手机号' }, { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }]}
            >
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
            <Form.Item name="level_id" label="会员等级">
              <Select placeholder="请选择会员等级">
                <Select.Option value={1}>普通会员</Select.Option>
                <Select.Option value={2}>银卡会员</Select.Option>
                <Select.Option value={3}>金卡会员</Select.Option>
                <Select.Option value={4}>钻石会员</Select.Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建会员
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}