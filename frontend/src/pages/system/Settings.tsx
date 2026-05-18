import { useState } from 'react';
import { Card, Form, Input, Button, Select, InputNumber, Switch, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';

export default function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const onFinish = () => {
    setLoading(true);
    setTimeout(() => {
      message.success('保存成功');
      setLoading(false);
    }, 1000);
  };

  return (
    <Card title="系统配置">
      <Form form={form} onFinish={onFinish} layout="vertical" size="large">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>
          <div>
            <h3 style={{ marginBottom: '16px', color: '#1890ff' }}>基本设置</h3>
            <Form.Item label="系统名称" name="system_name" initialValue="FitAI智能健身管理系统">
              <Input />
            </Form.Item>
            <Form.Item label="门店名称" name="store_name" initialValue="FitAI旗舰店">
              <Input />
            </Form.Item>
            <Form.Item label="联系电话" name="phone" initialValue="400-888-8888">
              <Input />
            </Form.Item>
            <Form.Item label="地址" name="address" initialValue="北京市朝阳区xxx街道xxx号">
              <Input />
            </Form.Item>
          </div>
          <div>
            <h3 style={{ marginBottom: '16px', color: '#1890ff' }}>业务设置</h3>
            <Form.Item label="预约提前天数" name="booking_days" initialValue="7">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="取消预约时限(小时)" name="cancel_hours" initialValue="2">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="每日最大预约数" name="max_bookings" initialValue="100">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="开启会员冻结" name="enable_freeze" initialValue={true}>
              <Switch />
            </Form.Item>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px', marginTop: '24px' }}>
          <div>
            <h3 style={{ marginBottom: '16px', color: '#1890ff' }}>通知设置</h3>
            <Form.Item label="开启短信通知" name="enable_sms" initialValue={true}>
              <Switch />
            </Form.Item>
            <Form.Item label="开启微信通知" name="enable_wechat" initialValue={true}>
              <Switch />
            </Form.Item>
            <Form.Item label="课前提醒时间(分钟)" name="remind_before" initialValue="30">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <div>
            <h3 style={{ marginBottom: '16px', color: '#1890ff' }}>数据设置</h3>
            <Form.Item label="数据备份周期(天)" name="backup_days" initialValue="7">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="日志保留天数" name="log_days" initialValue="30">
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="自动清理过期数据" name="auto_clean" initialValue={true}>
              <Switch />
            </Form.Item>
          </div>
        </div>
        <Form.Item style={{ marginTop: '24px' }}>
          <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
            保存配置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}