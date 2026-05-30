import { get, put } from './request'
import type { MemberInfo, CardInfo, BodyTestRecord } from '@/types'

/** 获取会员资料 */
export function getProfile(): Promise<MemberInfo> {
  return get('/api/v1/member/profile')
}

/** 更新会员资料 */
export function updateProfile(data: Partial<MemberInfo>): Promise<MemberInfo> {
  return put('/api/v1/member/profile', data, { showLoading: true })
}

/** 获取会员卡信息 */
export function getCardInfo(): Promise<CardInfo> {
  return get('/api/v1/member/card')
}

/** 获取体型测试记录 */
export function getBodyTestRecords(): Promise<BodyTestRecord[]> {
  return get('/api/v1/member/body-tests')
}

/** 获取签到二维码 */
export function getCheckinQRCode(): Promise<{ qrcode: string; token: string; expires_in: number }> {
  return get('/api/v1/mini/checkin/qrcode')
}
