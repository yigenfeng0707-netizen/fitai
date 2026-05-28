import { Form, Input, Button, Card, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api'

const Login = () => {
  const navigate = useNavigate()
  const [loginForm] = Form.useForm()
  const [registerForm] = Form.useForm()

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      const res = await authApi.login(values)
      localStorage.setItem('token', res.access_token)
      const user = await authApi.getCurrentUser()
      localStorage.setItem('user', JSON.stringify(user))
      message.success('登录成功')
      navigate('/')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败')
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    try {
      await authApi.register({ username: values.username, email: values.email, password: values.password, role: 'receptionist' })
      message.success('注册成功，请登录')
      registerForm.resetFields()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败')
    }
  }

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card style={{ width: 420, borderRadius: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: 24, color: '#333' }}>FitAI</h1>
          <p style={{ margin: '8px 0 0', color: '#888', fontSize: 14 }}>健身瑜伽教培管理系统</p>
        </div>

        <Tabs
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} onFinish={handleLogin} layout="vertical" size="large">
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名或邮箱' }]}>
                    <Input prefix={<UserOutlined />} placeholder="用户名 / 邮箱" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                  </Form.Item>
                  <Form.Item style={{ marginBottom: 8 }}>
                    <Button type="primary" htmlType="submit" block>登录</Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form form={registerForm} onFinish={handleRegister} layout="vertical" size="large">
                  <Form.Item name="username" rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}>
                    <Input prefix={<UserOutlined />} placeholder="用户名" />
                  </Form.Item>
                  <Form.Item name="email" rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入正确的邮箱格式' },
                  ]}>
                    <Input prefix={<MailOutlined />} placeholder="邮箱" />
                  </Form.Item>
                  <Form.Item name="password" rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' },
                  ]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                  </Form.Item>
                  <Form.Item name="confirm" dependencies={['password']} rules={[
                    { required: true, message: '请确认密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) return Promise.resolve()
                        return Promise.reject(new Error('两次密码不一致'))
                      },
                    }),
                  ]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
                  </Form.Item>
                  <Form.Item style={{ marginBottom: 8 }}>
                    <Button type="primary" htmlType="submit" block>注册</Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />

        <div style={{ textAlign: 'center', color: '#bbb', fontSize: 12, marginTop: 8 }}>
          FitAI v1.0.0
        </div>
      </Card>
    </div>
  )
}

export default Login
