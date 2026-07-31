import { get, post } from './request'
import type { OrderInfo, CreateOrderParams, PaginatedData, PaginationParams } from '@/types'

/** 创建支付订单 */
export function createOrder(data: CreateOrderParams): Promise<OrderInfo> {
  return post('/api/v1/orders', data, { showLoading: true })
}

/** 发起微信支付 */
export async function wxPay(orderId: number): Promise<void> {
  // 1. 获取支付参数
  const payParams = await post<any>('/api/v1/orders/pay', { orderId })

  // 2. 调用微信支付
  await Taro.requestPayment({
    timeStamp: payParams.timeStamp,
    nonceStr: payParams.nonceStr,
    package: payParams.package,
    signType: payParams.signType as any,
    paySign: payParams.paySign,
  })
}

/** 获取订单列表 */
export function getOrderList(params?: Partial<PaginationParams>): Promise<PaginatedData<OrderInfo>> {
  return get('/api/v1/orders', params)
}

/** 获取订单详情 */
export function getOrderDetail(orderId: number): Promise<OrderInfo> {
  return get(`/api/v1/orders/${orderId}`)
}
