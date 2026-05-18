import { useEffect, useState } from 'react';
import { Form, Input, Button, Card, Select, message, Row, Col, InputNumber } from 'antd';
import { ArrowLeftOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { courses } from '@/services/api';
import { useNavigate } from 'umi';

export default function CreateCourse() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const result = await courses.categories();
      setCategories(result);
    } catch (error) {
      message.error('获取分类失败');
    }
  };

  const onFinish = async (values: { name: string; category_id: number; course_type: string; duration: number; price: number; max_capacity?: number }) => {
    setLoading(true);
    try {
      await courses.create(values);
      message.success('课程创建成功');
      navigate('/courses');
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="新增课程"
      extra={
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/courses')}>
          返回列表
        </Button>
      }
    >
      <Form form={form} onFinish={onFinish} layout="vertical" size="large">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="name"
              label="课程名称"
              rules={[{ required: true, message: '请输入课程名称' }]}
            >
              <Input prefix={<ClockCircleOutlined />} placeholder="请输入课程名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="category_id"
              label="课程分类"
              rules={[{ required: true, message: '请选择课程分类' }]}
            >
              <Select placeholder="请选择课程分类">
                {categories.map((cat) => (
                  <Select.Option key={cat.id} value={cat.id}>
                    {cat.name}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="course_type"
              label="课程类型"
              rules={[{ required: true, message: '请选择课程类型' }]}
            >
              <Select placeholder="请选择课程类型">
                <Select.Option value="group">团课</Select.Option>
                <Select.Option value="private">私教</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="duration"
              label="时长(分钟)"
              rules={[{ required: true, message: '请输入时长' }]}
            >
              <InputNumber placeholder="请输入时长" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="price"
              label="价格(元)"
              rules={[{ required: true, message: '请输入价格' }]}
            >
              <InputNumber placeholder="请输入价格" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="max_capacity" label="最大人数">
              <InputNumber placeholder="请输入最大人数" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建课程
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}