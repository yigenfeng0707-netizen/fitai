import { View, Text, Button, Input } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState } from 'react'
import { wxLogin, phoneLogin, sendSmsCode } from '@/services/auth'
import './index.scss'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [smsCode, setSmsCode] = useState('')
  const [countdown, setCountdown] = useState(0)
  const [loginType, setLoginType] = useState<'wx' | 'phone'>('wx')
  const [loading, setLoading] = useState(false)

  /** 微信一键登录 */
  const handleWxLogin = async () => {
    setLoading(true)
    try {
      await wxLogin()
      Taro.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        Taro.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } catch (error: any) {
      Taro.showToast({ title: error.message || '登录失败', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }

  /** 发送验证码 */
  const handleSendCode = async () => {
    if (!phone || phone.length !== 11) {
      Taro.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    try {
      await sendSmsCode(phone)
      Taro.showToast({ title: '验证码已发送', icon: 'success' })

      // 开始倒计时
      setCountdown(60)
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } catch (error: any) {
      Taro.showToast({ title: error.message || '发送失败', icon: 'none' })
    }
  }

  /** 手机号登录 */
  const handlePhoneLogin = async () => {
    if (!phone || phone.length !== 11) {
      Taro.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    if (!smsCode || smsCode.length < 4) {
      Taro.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }

    setLoading(true)
    try {
      await phoneLogin(phone, smsCode)
      Taro.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        Taro.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } catch (error: any) {
      Taro.showToast({ title: error.message || '登录失败', icon: 'none' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className="page-login">
      {/* Logo 区域 */}
      <View className="login-header">
        <View className="login-header__logo">
          <Text className="login-header__logo-text">FitAI</Text>
        </View>
        <Text className="login-header__title">智能健身瑜伽管理</Text>
        <Text className="login-header__subtitle">登录后开始你的健身之旅</Text>
      </View>

      {/* 登录方式切换 */}
      <View className="login-tabs">
        <View
          className={`login-tabs__item ${loginType === 'wx' ? 'login-tabs__item--active' : ''}`}
          onClick={() => setLoginType('wx')}
        >
          <Text>微信登录</Text>
        </View>
        <View
          className={`login-tabs__item ${loginType === 'phone' ? 'login-tabs__item--active' : ''}`}
          onClick={() => setLoginType('phone')}
        >
          <Text>手机号登录</Text>
        </View>
      </View>

      {/* 登录表单 */}
      <View className="login-form">
        {loginType === 'wx' ? (
          <View className="login-form__wx">
            <Button
              className="login-form__wx-btn"
              openType="getPhoneNumber"
              loading={loading}
              onClick={handleWxLogin}
            >
              微信一键登录
            </Button>
          </View>
        ) : (
          <View className="login-form__phone">
            <View className="login-form__field">
              <Input
                className="login-form__input"
                type="number"
                placeholder="请输入手机号"
                maxlength={11}
                value={phone}
                onInput={(e) => setPhone(e.detail.value)}
              />
            </View>
            <View className="login-form__field login-form__field--code">
              <Input
                className="login-form__input"
                type="number"
                placeholder="请输入验证码"
                maxlength={6}
                value={smsCode}
                onInput={(e) => setSmsCode(e.detail.value)}
              />
              <View
                className={`login-form__code-btn ${countdown > 0 ? 'login-form__code-btn--disabled' : ''}`}
                onClick={countdown > 0 ? undefined : handleSendCode}
              >
                <Text className="login-form__code-text">
                  {countdown > 0 ? `${countdown}s` : '获取验证码'}
                </Text>
              </View>
            </View>
            <Button
              className="login-form__submit"
              loading={loading}
              onClick={handlePhoneLogin}
            >
              登录
            </Button>
          </View>
        )}
      </View>

      {/* 协议 */}
      <View className="login-agreement">
        <Text className="login-agreement__text">
          登录即表示同意
          <Text className="login-agreement__link">《用户协议》</Text>
          和
          <Text className="login-agreement__link">《隐私政策》</Text>
        </Text>
      </View>
    </View>
  )
}
