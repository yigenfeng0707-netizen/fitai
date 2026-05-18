import { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { auth } from '@/services/api';
import { useUser } from '@/store/user';
import styles from './Login.less';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const { login } = useUser();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response = await auth.login(values);
      localStorage.setItem('access_token', response.access_token);
      login({
        id: response.user_id,
        username: response.username,
        name: response.username,
        role_id: response.role_id,
        store_id: response.store_id,
      });
      message.success('登录成功');
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);
    } catch (error) {
      message.error('登录失败，请检查用户名或密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.login}>
      <Card className={styles.card}>
        <h2 className={styles.title}>FitAI 智能健身管理系统</h2>
        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
            />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading}
            >
              登录
            </Button>
          </Form.Item>
          <p className={styles.tip}>默认账号: admin / 密码: admin123</p>
        </Form>
      </Card>
    </div>
  );
}