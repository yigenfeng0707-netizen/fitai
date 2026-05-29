import Taro from '@tarojs/taro'

/** 存储键名 */
const KEYS = {
  TOKEN: 'fitai_token',
  USER_INFO: 'fitai_user_info',
  MEMBER_INFO: 'fitai_member_info',
  CURRENT_STORE: 'fitai_current_store',
} as const

/** 设置存储 */
export function setStorage<T>(key: string, value: T): Promise<void> {
  return Taro.setStorage({ key, data: value })
}

/** 获取存储 */
export function getStorage<T>(key: string): Promise<T> {
  return Taro.getStorage({ key }) as Promise<T>
}

/** 移除存储 */
export function removeStorage(key: string): Promise<void> {
  return Taro.removeStorage({ key })
}

/** 清除所有存储 */
export function clearStorage(): Promise<void> {
  return Taro.clearStorage()
}

/** Token 相关 */
export function getToken(): string {
  try {
    return Taro.getStorageSync(KEYS.TOKEN) || ''
  } catch {
    return ''
  }
}

export function setToken(token: string): Promise<void> {
  return setStorage(KEYS.TOKEN, token)
}

export function removeToken(): Promise<void> {
  return removeStorage(KEYS.TOKEN)
}

/** 用户信息 */
export function getUserInfo<T>(): Promise<T> {
  return getStorage<T>(KEYS.USER_INFO)
}

export function setUserInfo<T>(info: T): Promise<void> {
  return setStorage(KEYS.USER_INFO, info)
}

/** 会员信息 */
export function getMemberInfo<T>(): Promise<T> {
  return getStorage<T>(KEYS.MEMBER_INFO)
}

export function setMemberInfo<T>(info: T): Promise<void> {
  return setStorage(KEYS.MEMBER_INFO, info)
}

/** 当前门店 */
export function getCurrentStore<T>(): Promise<T> {
  return getStorage<T>(KEYS.CURRENT_STORE)
}

export function setCurrentStore<T>(store: T): Promise<void> {
  return setStorage(KEYS.CURRENT_STORE, store)
}

/** 清除所有用户相关存储 */
export function clearUserStorage(): Promise<void> {
  return Promise.all([
    removeToken(),
    removeStorage(KEYS.USER_INFO),
    removeStorage(KEYS.MEMBER_INFO),
  ]).then(() => {})
}

export { KEYS }
