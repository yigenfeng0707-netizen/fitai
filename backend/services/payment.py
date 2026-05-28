from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
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
            trade_no=f"ALI{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
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


class WeChatPayGateway(PaymentGateway):
    async def create_payment(
        self,
        order_no: str,
        subject: str,
        amount: float,
        description: Optional[str] = None,
    ) -> PaymentResult:
        return PaymentResult(
            success=True,
            trade_no=f"WX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            redirect_url=f"{settings.WECHAT_PAY_GATEWAY_URL}?order_no={order_no}",
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


class PaymentService:
    def __init__(self):
        self._gateways: dict[str, PaymentGateway] = {}
        self._register_defaults()

    def _register_defaults(self):
        self._gateways["alipay"] = AlipayGateway()
        self._gateways["wechat"] = WeChatPayGateway()

    def register(self, method: str, gateway: PaymentGateway):
        self._gateways[method] = gateway

    def get_gateway(self, method: str) -> PaymentGateway:
        gateway = self._gateways.get(method)
        if not gateway:
            raise ValueError(f"不支持的支付方式: {method}")
        return gateway


payment_service = PaymentService()
