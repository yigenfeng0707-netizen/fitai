from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.config import settings


@dataclass
class PaymentResult:
    success: bool
    trade_no: Optional[str] = None
    redirect_url: Optional[str] = None
    raw: Optional[dict] = None
    message: Optional[str] = None


class PaymentGateway(ABC):
    @abstractmethod
    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        ...

    @abstractmethod
    async def verify_notification(self, data: dict) -> dict:
        ...

    @abstractmethod
    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentResult:
        ...

    @abstractmethod
    async def query(self, order_no: str) -> PaymentResult:
        ...


class AlipayGateway(PaymentGateway):
    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            trade_no=f"ALI{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            redirect_url=f"{settings.ALIPAY_GATEWAY_URL}?order_no={order_no}",
        )

    async def verify_notification(self, data: dict) -> dict:
        if not data.get("order_no") or not data.get("trade_no"):
            raise ValueError("支付通知缺少必要字段: order_no, trade_no")
        return data

    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentResult:
        return PaymentResult(success=True, trade_no=f"REF{order_no}")

    async def query(self, order_no: str) -> PaymentResult:
        return PaymentResult(success=True, trade_no=order_no)


class CashGateway(PaymentGateway):
    """Cash/transfer payment - immediate confirmation."""

    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            trade_no=f"CASH{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            message="Cash payment - confirm at counter",
        )

    async def verify_notification(self, data: dict) -> dict:
        return data

    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentResult:
        return PaymentResult(success=True, trade_no=f"REF{order_no}", message="Cash refund processed")

    async def query(self, order_no: str) -> PaymentResult:
        return PaymentResult(success=True, trade_no=order_no)


class AlipayFaceGateway(PaymentGateway):
    """Alipay 当面付 - personal developer supported."""

    def __init__(self):
        from backend.services.alipay import alipay_client as client
        self._client = client

    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        if not self._client._enabled:
            import time
            return PaymentResult(
                success=True,
                trade_no=f"ALI{int(time.time())}",
                message="Alipay not configured - stub mode",
            )
        try:
            result = await self._client.create_qr_payment(order_no, subject, amount, description or "")
            return PaymentResult(
                success=True,
                trade_no=order_no,
                redirect_url=result.get("qr_code", ""),
                raw={"qr_code": result.get("qr_code", ""), "type": "alipay_qr", "stub": result.get("stub", False)},
            )
        except Exception as e:
            return PaymentResult(success=False, message=str(e))

    async def verify_notification(self, data: dict) -> dict:
        headers = data.get("headers", {})
        body = data.get("body", "")
        if not self._client._enabled:
            return data
        return self._client.verify_notification(headers, body)

    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentResult:
        if not self._client._enabled:
            import time
            return PaymentResult(success=True, trade_no=f"ALIREF{int(time.time())}")
        try:
            result = await self._client.refund(order_no, amount, reason or "")
            return PaymentResult(success=True, trade_no=result.get("trade_no", ""), raw=result)
        except Exception as e:
            return PaymentResult(success=False, message=str(e))

    async def query(self, order_no: str) -> PaymentResult:
        if not self._client._enabled:
            return PaymentResult(success=True, trade_no=order_no)
        try:
            result = await self._client.query_order(order_no)
            return PaymentResult(
                success=result.get("trade_state") == "TRADE_SUCCESS",
                trade_no=result.get("trade_no", ""),
                raw=result,
            )
        except Exception as e:
            return PaymentResult(success=False, message=str(e))


class WeChatPayGateway(PaymentGateway):
    def __init__(self):
        from backend.services.wechat_pay_v3 import wechat_pay_v3 as v3
        self._v3 = v3

    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        if not self._v3._enabled:
            return PaymentResult(
                success=True,
                trade_no=f"WX{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                message="WeChat Pay not configured — stub mode",
            )
        try:
            result = await self._v3.create_native_payment(
                order_no, subject, amount, description or "",
            )
            return PaymentResult(
                success=True,
                trade_no=order_no,
                redirect_url=result.get("code_url", ""),
                raw={"code_url": result.get("code_url", ""), "type": "native"},
            )
        except Exception as e:
            return PaymentResult(success=False, message=str(e))

    async def verify_notification(self, data: dict) -> dict:
        """Verify WeChat Pay V3 notification. data should contain 'headers' and 'body'."""
        headers = data.get("headers", {})
        body_str = data.get("body", "")
        if not self._v3._enabled:
            if not data.get("order_no") or not data.get("trade_no"):
                raise ValueError("支付通知缺少必要字段: order_no, trade_no")
            return data
        try:
            return self._v3.verify_notification(headers, body_str)
        except Exception as e:
            from backend.logger import logger
            logger.warning(f"WeChat Pay V3 notification verification failed: {e}")
            raise ValueError(f"通知验签失败: {e}")

    async def refund(
        self,
        order_no: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> PaymentResult:
        if not self._v3._enabled:
            return PaymentResult(success=True, trade_no=f"REF{order_no}")
        try:
            result = await self._v3.refund(order_no, amount, reason or "")
            return PaymentResult(
                success=True,
                trade_no=result.get("refund_id", ""),
                raw=result,
            )
        except Exception as e:
            return PaymentResult(success=False, message=str(e))

    async def query(self, order_no: str) -> PaymentResult:
        if not self._v3._enabled:
            return PaymentResult(success=True, trade_no=order_no)
        try:
            result = await self._v3.query_order(order_no)
            return PaymentResult(
                success=result.get("trade_state") == "SUCCESS",
                trade_no=result.get("transaction_id", ""),
                raw=result,
            )
        except Exception as e:
            return PaymentResult(success=False, message=str(e))


class PaymentService:
    def __init__(self):
        self._gateways: dict[str, PaymentGateway] = {}
        self._register_defaults()

    def _register_defaults(self):
        self._gateways["alipay"] = AlipayGateway()
        self._gateways["alipay_face"] = AlipayFaceGateway()
        self._gateways["wechat"] = WeChatPayGateway()
        self._gateways["cash"] = CashGateway()
        self._gateways["transfer"] = CashGateway()

    def register(self, method: str, gateway: PaymentGateway):
        self._gateways[method] = gateway

    def get_gateway(self, method: str) -> PaymentGateway:
        gateway = self._gateways.get(method)
        if not gateway:
            raise ValueError(f"不支持的支付方式: {method}")
        return gateway


payment_service = PaymentService()
