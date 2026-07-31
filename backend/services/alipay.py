"""
支付宝当面付 (Face-to-Face Payment) 客户端
使用 python-alipay-sdk 库，支持个人开发者账号
"""
import json
from typing import Optional

from backend.config import settings
from backend.logger import logger


class AlipayClient:
    def __init__(self):
        self._app_id = settings.ALIPAY_APP_ID
        self._private_key = settings.ALIPAY_PRIVATE_KEY
        self._alipay_public_key = settings.ALIPAY_PUBLIC_KEY
        self._notify_url = settings.ALIPAY_NOTIFY_URL
        self._gateway_url = settings.ALIPAY_GATEWAY_URL
        self._enabled = bool(self._app_id and self._private_key and self._alipay_public_key)

    def _get_sdk(self):
        if not self._enabled:
            raise RuntimeError("Alipay not configured (need APP_ID, PRIVATE_KEY, PUBLIC_KEY)")
        from alipay import AliPay
        return AliPay(
            appid=self._app_id,
            app_notify_url=self._notify_url,
            app_private_key_string=self._private_key,
            alipay_public_key_string=self._alipay_public_key,
            sign_type="RSA2",
            debug=(settings.APP_ENV != "production"),
        )

    async def create_qr_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: str = "",
    ) -> dict:
        """Create a QR code payment via alipay.trade.precreate."""
        if not self._enabled:
            import time
            return {
                "qr_code": f"https://qr.alipay.com/stub_{order_no}",
                "trade_no": f"ALI{int(time.time())}",
                "stub": True,
            }
        try:
            sdk = self._get_sdk()
            result = sdk.api_alipay_trade_precreate(
                subject=(subject or description)[:128],
                out_trade_no=order_no,
                total_amount=f"{amount:.2f}",
                time_expire="30m",
                notify_url=self._notify_url,
            )
            if result.get("code") == "10000":
                return {
                    "qr_code": result.get("qr_code", ""),
                    "trade_no": result.get("trade_no", ""),
                    "stub": False,
                }
            else:
                msg = result.get("sub_msg") or result.get("msg", "Unknown error")
                raise RuntimeError(f"Alipay precreate failed: {msg}")
        except Exception as e:
            logger.error(f"Alipay create_qr_payment error: {e}")
            raise

    async def query_order(self, order_no: str) -> dict:
        """Query order status via alipay.trade.query."""
        if not self._enabled:
            return {"trade_state": "UNKNOWN", "out_trade_no": order_no}
        try:
            sdk = self._get_sdk()
            result = sdk.api_alipay_trade_query(out_trade_no=order_no)
            return {
                "trade_state": result.get("trade_state", "UNKNOWN"),
                "trade_no": result.get("trade_no", ""),
                "out_trade_no": result.get("out_trade_no", order_no),
                "total_amount": result.get("total_amount", "0"),
                "buyer_pay_amount": result.get("buyer_pay_amount", "0"),
                "receipt_amount": result.get("receipt_amount", "0"),
            }
        except Exception as e:
            logger.error(f"Alipay query_order error: {e}")
            return {"trade_state": "ERROR"}

    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: str = "",
    ) -> dict:
        """Refund via alipay.trade.refund."""
        if not self._enabled:
            import time
            return {"trade_no": f"ALIREF{int(time.time())}", "stub": True}
        try:
            sdk = self._get_sdk()
            result = sdk.api_alipay_trade_refund(
                out_trade_no=order_no,
                refund_amount=f"{amount:.2f}",
                refund_reason=reason[:200],
            )
            if result.get("code") == "10000":
                return {
                    "trade_no": result.get("trade_no", ""),
                    "refund_fee": result.get("refund_fee", "0"),
                }
            else:
                msg = result.get("sub_msg") or result.get("msg", "Unknown error")
                raise RuntimeError(f"Alipay refund failed: {msg}")
        except Exception as e:
            logger.error(f"Alipay refund error: {e}")
            raise

    def verify_notification(self, headers: dict, body: str) -> dict:
        """Verify Alipay async notification signature."""
        if not self._enabled:
            return json.loads(body) if body else {}
        try:
            sdk = self._get_sdk()
            from urllib.parse import parse_qs
            params = parse_qs(body)
            # Flatten single-value lists
            flat_params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in params.items()}
            verified = sdk.verify(flat_params)
            if not verified:
                raise RuntimeError("Alipay notification signature verification failed")
            return flat_params
        except Exception as e:
            logger.error(f"Alipay verify_notification error: {e}")
            raise


alipay_client = AlipayClient()
