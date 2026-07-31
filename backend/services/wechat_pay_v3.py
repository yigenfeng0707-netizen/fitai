"""
微信支付 V3 官方 API 实现
"""
import json
import time
from typing import Optional

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography import x509

from backend.config import settings
from backend.logger import logger


class WeChatPayV3Error(Exception):
    pass


def _load_private_key(path: str) -> Optional[rsa.RSAPrivateKey]:
    try:
        with open(path, "rb") as f:
            key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend(),
            )
            if isinstance(key, rsa.RSAPrivateKey):
                return key
            logger.warning("WeChat Pay private key is not an RSA key")
            return None
    except Exception as e:
        logger.warning(f"Failed to load WeChat Pay private key: {e}")
        return None


def _decrypt_aead(associated_data: str, nonce: str, ciphertext: str) -> dict:
    from base64 import b64decode
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = settings.WECHAT_PAY_API_V3_KEY.encode("utf-8")
    if not key:
        raise WeChatPayV3Error("WECHAT_PAY_API_V3_KEY not configured")
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(
        b64decode(nonce), b64decode(ciphertext),
        associated_data.encode("utf-8"),
    )
    return json.loads(plaintext.decode("utf-8"))


class WeChatPayV3Client:
    def __init__(self):
        self._app_id = settings.WECHAT_PAY_APP_ID
        self._mch_id = settings.WECHAT_PAY_MCH_ID
        self._api_v3_key = settings.WECHAT_PAY_API_V3_KEY
        self._notify_url = settings.WECHAT_PAY_NOTIFY_URL
        self._base_url = settings.WECHAT_PAY_GATEWAY_URL.rstrip("/")
        self._cert_serial_no = settings.WECHAT_PAY_CERT_SERIAL_NO
        self._private_key_path = settings.WECHAT_PAY_PRIVATE_KEY_PATH

        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._platform_certs: dict[str, rsa.RSAPublicKey] = {}
        self._enabled = bool(self._mch_id and self._api_v3_key and self._private_key_path)

    def _get_private_key(self) -> rsa.RSAPrivateKey:
        if self._private_key is None:
            if not self._private_key_path:
                raise WeChatPayV3Error("WECHAT_PAY_PRIVATE_KEY_PATH not configured")
            pk = _load_private_key(self._private_key_path)
            if pk is None:
                raise WeChatPayV3Error("Failed to load WeChat Pay private key")
            self._private_key = pk
        return self._private_key

    def _sign(self, method: str, url: str, body: str = "") -> str:
        key = self._get_private_key()
        ts = str(int(time.time()))
        nonce = str(int(time.time() * 1000000))
        message = f"{method}\n{url}\n{ts}\n{nonce}\n{body}\n"
        signature = key.sign(
            message.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256(),
        )
        return (
            f'mchid="{self._mch_id}",nonce_str="{nonce}",'
            f'timestamp="{ts}",serial_no="{self._cert_serial_no}",'
            f'signature="{signature.hex()}"'
        )

    def _request_platform_certificates(self) -> dict[str, rsa.RSAPublicKey]:
        token = self._sign("GET", "/v3/certificates")
        with httpx.Client(verify=True) as client:
            resp = client.get(
                f"{self._base_url}/v3/certificates",
                headers={
                    "Authorization": f"WECHATPAY2-SHA256-RSA2048 {token}",
                    "User-Agent": "FitAI/1.0",
                },
            )
        if resp.status_code != 200:
            raise WeChatPayV3Error(
                f"Failed to fetch platform certs: {resp.status_code} {resp.text}",
            )
        data = resp.json()
        certs: dict[str, rsa.RSAPublicKey] = {}
        for item in data.get("data", []):
            enc = item["encrypt_certificate"]
            cert_info = _decrypt_aead(
                enc["associated_data"], enc["nonce"], enc["ciphertext"],
            )
            cert_pem = cert_info.get("certificate", "") if isinstance(cert_info, dict) else ""
            if not cert_pem:
                continue
            cert_obj = x509.load_pem_x509_certificate(
                cert_pem.encode("utf-8"), default_backend(),
            )
            pub = cert_obj.public_key()
            if isinstance(pub, rsa.RSAPublicKey):
                certs[item["serial_no"]] = pub
        return certs

    def _get_platform_public_key(self, serial_no: str) -> Optional[rsa.RSAPublicKey]:
        if serial_no not in self._platform_certs:
            try:
                self._platform_certs = self._request_platform_certificates()
            except Exception as e:
                logger.warning(f"Failed to refresh platform certs: {e}")
                return None
        return self._platform_certs.get(serial_no)

    def _call_api(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        if not self._enabled:
            raise WeChatPayV3Error(
                "WeChat Pay not configured "
                "(need MCH_ID, API_V3_KEY, and PRIVATE_KEY_PATH)",
            )
        body_str = json.dumps(body, separators=(",", ":")) if body else ""
        token = self._sign(method, path, body_str)

        with httpx.Client(verify=True, timeout=15) as client:
            resp = client.request(
                method,
                f"{self._base_url}{path}",
                headers={
                    "Authorization": f"WECHATPAY2-SHA256-RSA2048 {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "FitAI/1.0",
                },
                content=body_str if body else None,
            )

        if resp.status_code not in (200, 201, 204):
            raise WeChatPayV3Error(
                f"WeChat Pay API error {resp.status_code}: {resp.text}",
            )
        return resp.json() if resp.content else {}

    async def create_native_payment(
        self, order_no: str, subject: str, amount: float, description: str = "",
    ) -> dict:
        total = int(round(amount * 100))
        body = {
            "appid": self._app_id,
            "mchid": self._mch_id,
            "description": (subject or description)[:127],
            "out_trade_no": order_no,
            "notify_url": self._notify_url,
            "amount": {"total": total, "currency": "CNY"},
        }
        result = self._call_api("POST", "/v3/pay/transactions/native", body)
        return {
            "code_url": result.get("code_url", ""),
            "prepay_id": result.get("prepay_id", ""),
        }

    async def create_jsapi_payment(
        self, order_no: str, subject: str, amount: float,
        open_id: str, description: str = "",
    ) -> dict:
        total = int(round(amount * 100))
        body = {
            "appid": self._app_id,
            "mchid": self._mch_id,
            "description": (subject or description)[:127],
            "out_trade_no": order_no,
            "notify_url": self._notify_url,
            "amount": {"total": total, "currency": "CNY"},
            "payer": {"openid": open_id},
        }
        result = self._call_api("POST", "/v3/pay/transactions/jsapi", body)
        prepay_id = result.get("prepay_id", "")
        if not prepay_id:
            raise WeChatPayV3Error("JSAPI payment failed: no prepay_id returned")
        return self._build_jsapi_params(prepay_id)

    def _build_jsapi_params(self, prepay_id: str) -> dict:
        ts = str(int(time.time()))
        nonce = str(int(time.time() * 1000000))
        package = f"prepay_id={prepay_id}"
        message = f"{self._app_id}\n{ts}\n{nonce}\n{package}\n"
        key = self._get_private_key()
        signature = key.sign(
            message.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256(),
        )
        return {
            "appId": self._app_id,
            "timeStamp": ts,
            "nonceStr": nonce,
            "package": package,
            "signType": "RSA",
            "paySign": signature.hex(),
        }

    async def query_order(self, order_no: str) -> dict:
        return self._call_api(
            "GET",
            f"/v3/pay/transactions/out-trade-no/{order_no}?mchid={self._mch_id}",
        )

    async def close_order(self, order_no: str) -> None:
        self._call_api(
            "POST",
            f"/v3/pay/transactions/out-trade-no/{order_no}/close",
            {"mchid": self._mch_id},
        )

    async def refund(
        self, order_no: str, amount: float, reason: str = "",
    ) -> dict:
        total = int(round(amount * 100))
        body = {
            "out_trade_no": order_no,
            "out_refund_no": f"REF{order_no}{int(time.time())}",
            "reason": reason[:80],
            "amount": {"refund": total, "total": total, "currency": "CNY"},
        }
        return self._call_api("POST", "/v3/refund/domestic/refunds", body)

    def verify_notification(self, headers: dict, body: str) -> dict:
        serial_no = headers.get("Wechatpay-Serial", "")
        signature = headers.get("Wechatpay-Signature", "")
        timestamp = headers.get("Wechatpay-Timestamp", "")
        nonce = headers.get("Wechatpay-Nonce", "")

        if not all([serial_no, signature, timestamp, nonce]):
            raise WeChatPayV3Error("Missing WeChat Pay notification headers")

        message = f"{timestamp}\n{nonce}\n{body}\n"
        public_key = self._get_platform_public_key(serial_no)
        if public_key is None:
            raise WeChatPayV3Error(f"Unknown platform cert serial: {serial_no}")

        try:
            public_key.verify(
                bytes.fromhex(signature),
                message.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception as e:
            raise WeChatPayV3Error(
                f"Notification signature verification failed: {e}",
            )

        data = json.loads(body)
        resource = data.get("resource", {})
        return _decrypt_aead(
            resource.get("associated_data", ""),
            resource.get("nonce", ""),
            resource.get("ciphertext", ""),
        )


wechat_pay_v3 = WeChatPayV3Client()
