import { Form, Input, Button, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import '../styles/theme.css'

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
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background decorative circles */}
      <div style={{
        position: 'absolute', top: '-20%', left: '-10%', width: 500, height: 500,
        borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
        animation: 'pulse-glow 4s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute', bottom: '-15%', right: '-5%', width: 400, height: 400,
        borderRadius: '50%', background: 'radial-gradient(circle, rgba(168,85,247,0.12) 0%, transparent 70%)',
        animation: 'pulse-glow 5s ease-in-out infinite 1s',
      }} />
      <div style={{
        position: 'absolute', top: '40%', left: '60%', width: 300, height: 300,
        borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)',
        animation: 'pulse-glow 6s ease-in-out infinite 2s',
      }} />

      <div style={{
        width: 440, position: 'relative', zIndex: 1,
        background: 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(40px)',
        WebkitBackdropFilter: 'blur(40px)',
        borderRadius: 24,
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 32px 64px rgba(0, 0, 0, 0.3)',
        padding: '40px 36px',
        animation: 'fadeInUp 0.6s ease-out',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 900, color: '#fff', fontSize: 24,
            boxShadow: '0 8px 24px rgba(168, 85, 247, 0.4)',
            marginBottom: 16,
          }}>F</div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: 1 }}>FitAI</h1>
          <p style={{ margin: '8px 0 0', color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>
            健身瑜伽教培智能管理平台
          </p>
        </div>

        <Tabs
          centered
          style={{ '--tab-color': '#a855f7' } as React.CSSProperties}
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} onFinish={handleLogin} layout="vertical" size="large">
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名或邮箱' }]} style={{ marginBottom: 16 }}>
                    <Input
                      prefix={<UserOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="用户名 / 邮箱"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]} style={{ marginBottom: 20 }}>
                    <Input.Password
                      prefix={<LockOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="密码"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item style={{ marginBottom: 0 }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      block
                      size="large"
                      style={{
                        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                        border: 'none',
                        borderRadius: 12,
                        fontWeight: 600,
                        fontSize: 15,
                        height: 48,
                      }}
                    >登录</Button>
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
                  ]} style={{ marginBottom: 12 }}>
                    <Input
                      prefix={<UserOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="用户名"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item name="email" rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入正确的邮箱格式' },
                  ]} style={{ marginBottom: 12 }}>
                    <Input
                      prefix={<MailOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="邮箱"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item name="password" rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' },
                  ]} style={{ marginBottom: 12 }}>
                    <Input.Password
                      prefix={<LockOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="密码"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item name="confirm" dependencies={['password']} rules={[
                    { required: true, message: '请确认密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('password') === value) return Promise.resolve()
                        return Promise.reject(new Error('两次密码不一致'))
                      },
                    }),
                  ]} style={{ marginBottom: 20 }}>
                    <Input.Password
                      prefix={<LockOutlined style={{ color: '#8b5cf6' }} />}
                      placeholder="确认密码"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        color: '#fff',
                        borderRadius: 12,
                      }}
                    />
                  </Form.Item>
                  <Form.Item style={{ marginBottom: 0 }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      block
                      size="large"
                      style={{
                        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                        border: 'none',
                        borderRadius: 12,
                        fontWeight: 600,
                        fontSize: 15,
                        height: 48,
                      }}
                    >注册</Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />

        <div style={{
          textAlign: 'center', color: 'rgba(255,255,255,0.25)', fontSize: 11, marginTop: 16,
        }}>
          FitAI v1.0.0 · Powered by AI
        </div>
      </div>
    </div>
  )
}

export default Login
