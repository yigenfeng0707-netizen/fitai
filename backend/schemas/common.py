"""
通用响应 Schema
"""
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel


T = TypeVar("T")


class BaseResponse(BaseModel):
    """基础响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None


class ListResponse(BaseModel, Generic[T]):
    """列表响应"""
    success: bool = True
    message: str = "查询成功"
    data: list[T]
    total: int
    page: int = 1
    page_size: int = 20