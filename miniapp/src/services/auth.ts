import Taro from '@tarojs/taro'
import { post } from './request'
import { getToken, setToken, setUserInfo, setMemberInfo, clearUserStorage } from '@/utils/storage'
import type { LoginResponse } from '@/types'

/** 微信登录 - 获取 code 发送到后端换取 token */
export async function wxLogin(): Promise<LoginResponse> {
  // 1. 调用微信登录获取 code
  const loginRes = await Taro.login()
  if (!loginRes.code) {
    throw new Error('微信登录失败')
  }

  // 2. 将 code 发送到后端
  const data = await post<LoginResponse>('/api/v1/auth/wx-login', {
    code: loginRes.code,
  }, { showLoading: true })

  // 3. 保存登录信息
  await setToken(data.token)
  if (data.userInfo) {
    await setUserInfo(data.userInfo)
  }
  if (data.memberInfo) {
    await setMemberInfo(data.memberInfo)
  }

  return data
}

/** 手机号登录 */
export async function phoneLogin(phone: string, code: string): Promise<LoginResponse> {
  const data = await post<LoginResponse>('/api/v1/auth/phone-login', {
    phone,
    code,
  }, { showLoading: true })

  await setToken(data.token)
  if (data.userInfo) {
    await setUserInfo(data.userInfo)
  }
  if (data.memberInfo) {
    await setMemberInfo(data.memberInfo)
  }

  return data
}

/** 获取手机验证码 */
export async function sendSmsCode(phone: string): Promise<void> {
  await post('/api/v1/auth/send-code', { phone }, { showLoading: true })
}

/** 退出登录 */
export async function logout(): Promise<void> {
  try {
    await post('/api/v1/auth/logout')
  } finally {
    await clearUserStorage()
  }
}

/** 获取当前 token */
export function isLoggedIn(): boolean {
  return !!getToken()
}
