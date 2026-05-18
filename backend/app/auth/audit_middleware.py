"""
FitAI - 审计日志中间件
Phase 5: 操作日志审计增强
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Set
import re

from app.auth.audit import (
    get_audit_logger,
    AuditAction,
    AuditResource
)
from app.auth.rate_limit import RateLimiter


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件
    
    自动记录关键API操作
    """
    
    # 不记录的路径
    EXCLUDE_PATHS: Set[str] = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico"
    }
    
    # 路径审计规则
    PATH_AUDIT_RULES = [
        # 认证相关
        (re.compile(r"^/api/v1/auth/login$"), "POST", AuditAction.LOGIN_SUCCESS, AuditResource.USER),
        (re.compile(r"^/api/v1/auth/logout$"), "POST", AuditAction.LOGOUT, AuditResource.USER),
        
        # 会员管理
        (re.compile(r"^/api/v1/members$"), "POST", AuditAction.MEMBER_CREATE, AuditResource.MEMBER),
        (re.compile(r"^/api/v1/members/\d+$"), "PUT", AuditAction.MEMBER_UPDATE, AuditResource.MEMBER),
        (re.compile(r"^/api/v1/members/\d+$"), "DELETE", AuditAction.MEMBER_DELETE, AuditResource.MEMBER),
        
        # 课程管理
        (re.compile(r"^/api/v1/courses$"), "POST", AuditAction.COURSE_CREATE, AuditResource.COURSE),
        (re.compile(r"^/api/v1/courses/\d+$"), "PUT", AuditAction.COURSE_UPDATE, AuditResource.COURSE),
        (re.compile(r"^/api/v1/courses/\d+$"), "DELETE", AuditAction.COURSE_DELETE, AuditResource.COURSE),
        
        # 预约管理
        (re.compile(r"^/api/v1/bookings$"), "POST", AuditAction.BOOKING_CREATE, AuditResource.BOOKING),
        (re.compile(r"^/api/v1/bookings/\d+$"), "DELETE", AuditAction.BOOKING_DELETE, AuditResource.BOOKING),
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method
        
        # 检查是否排除
        if self._is_excluded(path):
            return await call_next(request)
        
        # 获取用户信息
        user_id = None
        username = None
        tenant_id = None
        
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.get('sub')
            username = request.state.user.get('username')
        
        if hasattr(request.state, 'tenant_id'):
            tenant_id = request.state.tenant_id
        
        # 获取客户端信息
        ip_address = RateLimiter._get_client_ip(request)
        user_agent = request.headers.get('User-Agent')
        
        # 匹配审计规则
        audit_rule = self._match_audit_rule(path, method)
        
        # 执行请求
        response = await call_next(request)
        
        # 如果有审计规则且请求成功，记录日志
        if audit_rule and 200 <= response.status_code < 300:
            action, resource = audit_rule
            
            # 尝试从路径中提取资源ID
            resource_id = self._extract_resource_id(path)
            
            try:
                logger = get_audit_logger()
                logger.log(
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    user_id=user_id,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    tenant_id=tenant_id,
                    method=method,
                    path=path,
                    status_code=response.status_code
                )
            except Exception:
                # 审计日志记录失败不影响主流程
                pass
        
        return response
    
    def _is_excluded(self, path: str) -> bool:
        """检查是否排除"""
        if path in self.EXCLUDE_PATHS:
            return True
        
        for prefix in ["/docs", "/openapi", "/static"]:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _match_audit_rule(self, path: str, method: str):
        """匹配审计规则"""
        for pattern, expected_method, action, resource in self.PATH_AUDIT_RULES:
            if pattern.match(path) and method == expected_method:
                return (action, resource)
        return None
    
    def _extract_resource_id(self, path: str):
        """从路径中提取资源ID"""
        parts = path.split('/')
        if parts and parts[-1].isdigit():
            return int(parts[-1])
        return None
