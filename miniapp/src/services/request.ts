import Taro from '@tarojs/taro'
import { BASE_URL, REQUEST_TIMEOUT } from '@/utils/constants'
import { getToken, removeToken } from '@/utils/storage'
import type { ApiResponse } from '@/types'

/** 请求配置 */
interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
  showLoading?: boolean
  showError?: boolean
}

/** 请求拦截 - 附加 token */
function getRequestHeader(): Record<string, string> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

/** 显示错误提示 */
function showErrorToast(message: string): void {
  Taro.showToast({
    title: message || '请求失败',
    icon: 'none',
    duration: 2000,
  })
}

/** 处理 401 未授权 */
function handleUnauthorized(): void {
  removeToken()
  Taro.redirectTo({ url: '/pages/login/index' })
}

/** 核心请求方法 */
export async function request<T = any>(config: RequestConfig): Promise<T> {
  const {
    url,
    method = 'GET',
    data,
    header = {},
    showLoading = false,
    showError = true,
  } = config

  if (showLoading) {
    Taro.showLoading({ title: '加载中...', mask: true })
  }

  try {
    const response = await Taro.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        ...getRequestHeader(),
        ...header,
      },
      timeout: REQUEST_TIMEOUT,
    })

    const res = response.data as ApiResponse<T>

    if (res.code === 0 || res.code === 200) {
      return res.data
    }

    // Token 过期或无效
    if (res.code === 401) {
      handleUnauthorized()
      throw new Error('登录已过期，请重新登录')
    }

    // 其他业务错误
    const errMsg = res.message || '请求失败'
    if (showError) {
      showErrorToast(errMsg)
    }
    throw new Error(errMsg)
  } catch (error: any) {
    // 网络错误
    if (error.message === 'request:fail') {
      if (showError) {
        showErrorToast('网络连接失败，请检查网络')
      }
      throw new Error('网络连接失败')
    }

    // 超时
    if (error.message?.includes('timeout')) {
      if (showError) {
        showErrorToast('请求超时，请重试')
      }
      throw new Error('请求超时')
    }

    throw error
  } finally {
    if (showLoading) {
      Taro.hideLoading()
    }
  }
}

/** GET 请求 */
export function get<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<T> {
  return request<T>({ url, method: 'GET', data, ...config })
}

/** POST 请求 */
export function post<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<T> {
  return request<T>({ url, method: 'POST', data, ...config })
}

/** PUT 请求 */
export function put<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<T> {
  return request<T>({ url, method: 'PUT', data, ...config })
}

/** DELETE 请求 */
export function del<T = any>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<T> {
  return request<T>({ url, method: 'DELETE', data, ...config })
}
