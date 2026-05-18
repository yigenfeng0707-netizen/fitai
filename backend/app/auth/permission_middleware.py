"""
FitAI - 全局权限中间件
Phase 2: 全局权限校验中间件
Phase 3: 多租户数据隔离
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Set
import re
from app.auth.security import AuthService
from app.auth.permissions import PermissionService, Role, Permission
from app.auth.tenant_context import TenantContext

class GlobalPermissionMiddleware(BaseHTTPMiddleware):
    """
    全局权限校验中间件
    对所有API请求进行权限校验和租户隔离
    """
    
    # 不需要认证的路径
    PUBLIC_PATHS = {
        "/",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
    }
    
    # 不需要认证的路径前缀
    PUBLIC_PATH_PREFIXES = [
        "/docs",
        "/openapi",
        "/static",
        "/favicon",
    ]
    
    # 权限配置：路径 -> 需要的权限
    PATH_PERMISSIONS: Dict[str, Set[Permission]] = {
        # 会员管理
        r"^/api/v1/members$": {Permission.MEMBER_READ},
        r"^/api/v1/members/\d+$": {Permission.MEMBER_READ, Permission.MEMBER_WRITE},
        r"^/api/v1/members/\d+$|DELETE": {Permission.MEMBER_DELETE},
        
        # 课程管理
        r"^/api/v1/courses$": {Permission.COURSE_READ},
        r"^/api/v1/courses/\d+$": {Permission.COURSE_READ, Permission.COURSE_WRITE},
        r"^/api/v1/courses/schedules": {Permission.COURSE_SCHEDULE},
        
        # 预约管理
        r"^/api/v1/bookings$": {Permission.BOOKING_READ},
        r"^/api/v1/bookings/signin": {Permission.BOOKING_SIGNIN},
        
        # 教练管理
        r"^/api/v1/coaches$": {Permission.COACH_READ},
        r"^/api/v1/coaches/\d+$": {Permission.COACH_READ, Permission.COACH_WRITE},
        r"^/api/v1/coaches/performance": {Permission.COACH_PERFORMANCE},
        
        # 财务管理
        r"^/api/v1/finance$": {Permission.FINANCE_READ},
        r"^/api/v1/finance/refund": {Permission.FINANCE_REFUND},
        r"^/api/v1/finance/export": {Permission.FINANCE_EXPORT},
        
        # 系统管理
        r"^/api/v1/system/config": {Permission.SYSTEM_CONFIG},
        r"^/api/v1/system/users": {Permission.SYSTEM_USER},
        r"^/api/v1/system/roles": {Permission.SYSTEM_ROLE},
        r"^/api/v1/system/audit": {Permission.SYSTEM_AUDIT},
        
        # 租户管理
        r"^/api/v1/tenants": {Permission.SYSTEM_ADMIN},
    }
    
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        method = request.method
        
        # 1. 检查是否是公开路径
        if self._is_public_path(path):
            return await call_next(request)
        
        # 2. 检查是否有Authorization头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # 如果是OPTIONS请求（CORS预检），放行
            if method == "OPTIONS":
                return await call_next(request)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "未提供认证令牌"}
            )
        
        # 3. 验证Token
        try:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            else:
                token = auth_header
            
            payload = AuthService.verify_token(token, token_type="access")
            if not payload:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "无效或过期的令牌"}
                )
            
            # 3.1 设置租户上下文
            tenant_id = payload.get("tenant_id")
            tenant_code = payload.get("tenant_code")
            TenantContext.set_tenant(tenant_id, tenant_code)
            request.state.tenant_id = tenant_id
            request.state.tenant_code = tenant_code
            
            # 4. 检查权限
            required_permissions = self._get_required_permissions(path, method)
            if required_permissions:
                role_id = payload.get("role_id", 3)
                has_permission = False
                
                for perm in required_permissions:
                    if PermissionService.has_permission(role_id, perm):
                        has_permission = True
                        break
                
                if not has_permission:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": f"没有权限访问此资源",
                            "required_permissions": [p.value for p in required_permissions]
                        }
                    )
            
            # 5. 将用户信息注入到request中
            request.state.user = payload
            
        except Exception as e:
            TenantContext.clear()
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"认证失败: {str(e)}"}
            )
        
        # 处理响应
        try:
            response = await call_next(request)
        finally:
            # 清除租户上下文
            TenantContext.clear()
        
        return response
    
    def _is_public_path(self, path: str) -> bool:
        """检查是否是公开路径"""
        # 精确匹配
        if path in self.PUBLIC_PATHS:
            return True
        
        # 前缀匹配
        for prefix in self.PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _get_required_permissions(self, path: str, method: str) -> Set[Permission]:
        """获取路径需要的权限"""
        required = set()
        
        for pattern, permissions in self.PATH_PERMISSIONS.items():
            if re.match(pattern, path):
                required.update(permissions)
        
        # 根据HTTP方法调整权限
        if method == "POST":
            # POST通常是创建，需要write权限
            pass
        elif method == "PUT" or method == "PATCH":
            # PUT/PATCH是更新，需要write权限
            pass
        elif method == "DELETE":
            # DELETE是删除，需要delete权限
            pass
        
        return required

class DataPermissionFilter:
    """
    数据权限过滤器
    根据用户角色和租户自动过滤查询结果
    """
    
    @staticmethod
    def apply_tenant_filter(query, model):
        """
        应用租户过滤
        非超级管理员只能看到自己租户的数据
        """
        tenant_id = TenantContext.get_tenant_id()
        
        # 超级管理员（tenant_id为None）可以看到所有
        if tenant_id is None:
            return query
        
        # 其他用户只能看到自己租户的数据
        return query.filter(model.tenant_id == tenant_id)
    
    @staticmethod
    def filter_members_query(query, current_user: dict):
        """
        过滤会员查询
        1. 租户隔离
        2. 教练只能看到自己的学员
        """
        from app.models.member import Member
        
        # 1. 租户隔离
        query = DataPermissionFilter.apply_tenant_filter(query, Member)
        
        role_id = current_user.get("role_id", 3)
        
        # 超级管理员/老板/前台/财务：可以看到所有
        if role_id in [1, 2, 3, 5]:
            return query
        
        # 教练：只能看到自己的学员
        if role_id == 4:
            user_id = current_user.get("sub")
            # 假设教练和学员有关联关系，这里简化处理
            # 实际应该通过 coach_id 字段过滤
            return query.filter(Member.coach_id == int(user_id))
        
        return query
    
    @staticmethod
    def filter_bookings_query(query, current_user: dict):
        """
        过滤预约查询
        1. 租户隔离
        2. 教练只能看到自己课程的预约
        """
        from app.models.booking import Booking
        
        # 1. 租户隔离
        query = DataPermissionFilter.apply_tenant_filter(query, Booking)
        
        role_id = current_user.get("role_id", 3)
        
        if role_id in [1, 2, 3, 5]:
            return query
        
        if role_id == 4:
            user_id = current_user.get("sub")
            # 假设预约和教练有关联
            return query.filter(Booking.coach_id == int(user_id))
        
        return query
    
    @staticmethod
    def filter_courses_query(query, current_user: dict):
        """
        过滤课程查询
        1. 租户隔离
        2. 教练只能看到自己教授的课程
        """
        from app.models.course import Course
        
        # 1. 租户隔离
        query = DataPermissionFilter.apply_tenant_filter(query, Course)
        
        role_id = current_user.get("role_id", 3)
        
        if role_id in [1, 2, 3, 5]:
            return query
        
        if role_id == 4:
            user_id = current_user.get("sub")
            # 假设课程和教练有关联
            return query.filter(Course.coach_id == int(user_id))
        
        return query
    
    @staticmethod
    def filter_coaches_query(query, current_user: dict):
        """
        过滤教练查询
        租户隔离
        """
        from app.models.coach import Coach
        return DataPermissionFilter.apply_tenant_filter(query, Coach)

def get_current_user(request: Request) -> dict:
    """从request中获取当前用户"""
    if hasattr(request.state, "user"):
        return request.state.user
    return None

def require_auth(current_user: dict = Depends(get_current_user)):
    """认证依赖"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    return current_user

def require_permission(*permissions: Permission):
    """
    权限依赖
    用法: Depends(require_permission(Permission.MEMBER_READ))
    """
    def dependency(current_user: dict = Depends(require_auth)):
        role_id = current_user.get("role_id", 3)
        
        for permission in permissions:
            if PermissionService.has_permission(role_id, permission):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限: {', '.join(p.value for p in permissions)}"
        )
    
    return dependency

def require_role(*roles: Role):
    """
    角色依赖
    用法: Depends(require_role(Role.SUPER_ADMIN))
    """
    def dependency(current_user: dict = Depends(require_auth)):
        role_id = current_user.get("role_id", 3)
        user_role = PermissionService.get_role_by_id(role_id)
        
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(r.value for r in roles)}"
            )
        
        return current_user
    
    return dependency
