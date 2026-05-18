from contextvars import ContextVar
from typing import Optional

# 租户上下文变量
_tenant_id: ContextVar[Optional[int]] = ContextVar('tenant_id', default=None)
_tenant_code: ContextVar[Optional[str]] = ContextVar('tenant_code', default=None)


class TenantContext:
    """租户上下文管理"""
    
    @staticmethod
    def set_tenant(tenant_id: Optional[int], tenant_code: Optional[str] = None):
        """设置当前租户"""
        _tenant_id.set(tenant_id)
        _tenant_code.set(tenant_code)
    
    @staticmethod
    def get_tenant_id() -> Optional[int]:
        """获取当前租户ID"""
        return _tenant_id.get()
    
    @staticmethod
    def get_tenant_code() -> Optional[str]:
        """获取当前租户编码"""
        return _tenant_code.get()
    
    @staticmethod
    def clear():
        """清除租户上下文"""
        _tenant_id.set(None)
        _tenant_code.set(None)
    
    @staticmethod
    def has_tenant() -> bool:
        """检查是否设置了租户"""
        return _tenant_id.get() is not None
