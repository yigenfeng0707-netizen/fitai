"""
自定义异常类
"""
from fastapi import status


class AppException(Exception):
    """应用基础异常"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"
    code: str = "internal_error"

    def __init__(self, detail: str | None = None, code: str | None = None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"
    code = "not_found"


class BusinessError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Business rule violation"
    code = "business_error"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"
    code = "authentication_error"


class PermissionDeniedError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
    code = "permission_denied"


class ValidationError_(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed"
    code = "validation_error"


class PaymentError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Payment service error"
    code = "payment_error"


class ExternalServiceError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "External service unavailable"
    code = "external_service_error"
