"""
FitAI - 权限系统核心模块
Phase 2: 全局权限校验中间件
"""
from enum import Enum
from typing import List, Optional, Set, Dict, Any
from functools import wraps
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session

class Permission(str, Enum):
    """资源权限枚举"""
    # 会员权限
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"
    MEMBER_DELETE = "member:delete"
    MEMBER_EXPORT = "member:export"
    
    # 课程权限
    COURSE_READ = "course:read"
    COURSE_WRITE = "course:write"
    COURSE_DELETE = "course:delete"
    COURSE_SCHEDULE = "course:schedule"
    
    # 预约权限
    BOOKING_READ = "booking:read"
    BOOKING_WRITE = "booking:write"
    BOOKING_SIGNIN = "booking:signin"
    
    # 教练权限
    COACH_READ = "coach:read"
    COACH_WRITE = "coach:write"
    COACH_PERFORMANCE = "coach:performance"
    
    # 财务权限
    FINANCE_READ = "finance:read"
    FINANCE_WRITE = "finance:write"
    FINANCE_REFUND = "finance:refund"
    FINANCE_EXPORT = "finance:export"
    
    # 营销权限
    MARKETING_READ = "marketing:read"
    MARKETING_WRITE = "marketing:write"
    
    # CRM权限
    CRM_READ = "crm:read"
    CRM_WRITE = "crm:write"
    CRM_ASSIGN = "crm:assign"
    
    # 系统权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_USER = "system:user"
    SYSTEM_ROLE = "system:role"
    SYSTEM_AUDIT = "system:audit"

class Role(str, Enum):
    """角色枚举"""
    SUPER_ADMIN = "super_admin"      # 超级管理员
    OWNER = "owner"                  # 老板/店长
    RECEPTION = "reception"          # 前台
    COACH = "coach"                  # 教练
    FINANCE = "finance"              # 财务

# 角色权限矩阵
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        # 超级管理员：拥有所有权限
        Permission.MEMBER_READ,
        Permission.MEMBER_WRITE,
        Permission.MEMBER_DELETE,
        Permission.MEMBER_EXPORT,
        Permission.COURSE_READ,
        Permission.COURSE_WRITE,
        Permission.COURSE_DELETE,
        Permission.COURSE_SCHEDULE,
        Permission.BOOKING_READ,
        Permission.BOOKING_WRITE,
        Permission.BOOKING_SIGNIN,
        Permission.COACH_READ,
        Permission.COACH_WRITE,
        Permission.COACH_PERFORMANCE,
        Permission.FINANCE_READ,
        Permission.FINANCE_WRITE,
        Permission.FINANCE_REFUND,
        Permission.FINANCE_EXPORT,
        Permission.MARKETING_READ,
        Permission.MARKETING_WRITE,
        Permission.CRM_READ,
        Permission.CRM_WRITE,
        Permission.CRM_ASSIGN,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_USER,
        Permission.SYSTEM_ROLE,
        Permission.SYSTEM_AUDIT,
    },
    Role.OWNER: {
        # 老板/店长：管理权限，无系统配置权限
        Permission.MEMBER_READ,
        Permission.MEMBER_WRITE,
        Permission.MEMBER_DELETE,
        Permission.MEMBER_EXPORT,
        Permission.COURSE_READ,
        Permission.COURSE_WRITE,
        Permission.COURSE_SCHEDULE,
        Permission.BOOKING_READ,
        Permission.BOOKING_WRITE,
        Permission.BOOKING_SIGNIN,
        Permission.COACH_READ,
        Permission.COACH_WRITE,
        Permission.COACH_PERFORMANCE,
        Permission.FINANCE_READ,
        Permission.MARKETING_READ,
        Permission.MARKETING_WRITE,
        Permission.CRM_READ,
        Permission.CRM_WRITE,
        Permission.SYSTEM_AUDIT,
    },
    Role.RECEPTION: {
        # 前台：会员服务和预约权限
        Permission.MEMBER_READ,
        Permission.MEMBER_WRITE,
        Permission.COURSE_READ,
        Permission.COURSE_SCHEDULE,
        Permission.BOOKING_READ,
        Permission.BOOKING_WRITE,
        Permission.BOOKING_SIGNIN,
        Permission.COACH_READ,
        Permission.CRM_READ,
        Permission.CRM_WRITE,
    },
    Role.COACH: {
        # 教练：课程和学员管理权限（仅限自己的）
        Permission.COURSE_READ,
        Permission.BOOKING_READ,
        Permission.BOOKING_SIGNIN,
        Permission.COACH_READ,
        Permission.COACH_PERFORMANCE,
    },
    Role.FINANCE: {
        # 财务：财务相关权限
        Permission.MEMBER_READ,
        Permission.COURSE_READ,
        Permission.BOOKING_READ,
        Permission.COACH_READ,
        Permission.FINANCE_READ,
        Permission.FINANCE_WRITE,
        Permission.FINANCE_REFUND,
        Permission.FINANCE_EXPORT,
    },
}

# 角色ID映射
ROLE_ID_MAP = {
    1: Role.SUPER_ADMIN,
    2: Role.OWNER,
    3: Role.RECEPTION,
    4: Role.COACH,
    5: Role.FINANCE,
}

class PermissionService:
    """权限服务"""
    
    @staticmethod
    def get_role_by_id(role_id: int) -> Role:
        """根据角色ID获取角色枚举"""
        return ROLE_ID_MAP.get(role_id, Role.RECEPTION)
    
    @staticmethod
    def get_role_permissions(role_id: int) -> Set[Permission]:
        """获取角色所有权限"""
        role = PermissionService.get_role_by_id(role_id)
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(role_id: int, permission: Permission) -> bool:
        """检查角色是否有指定权限"""
        permissions = PermissionService.get_role_permissions(role_id)
        return permission in permissions
    
    @staticmethod
    def has_any_permission(role_id: int, permissions: List[Permission]) -> bool:
        """检查角色是否有任一指定权限"""
        role_permissions = PermissionService.get_role_permissions(role_id)
        return any(p in role_permissions for p in permissions)
    
    @staticmethod
    def has_all_permissions(role_id: int, permissions: List[Permission]) -> bool:
        """检查角色是否有所有指定权限"""
        role_permissions = PermissionService.get_role_permissions(role_id)
        return all(p in role_permissions for p in permissions)
    
    @staticmethod
    def filter_permissions_by_role(role_id: int, permissions: List[Permission]) -> List[Permission]:
        """过滤出角色拥有的权限"""
        role_permissions = PermissionService.get_role_permissions(role_id)
        return [p for p in permissions if p in role_permissions]
    
    @staticmethod
    def is_super_admin(role_id: int) -> bool:
        """检查是否是超级管理员"""
        return role_id == 1
    
    @staticmethod
    def can_access_data(role_id: int, resource: str, owner_id: int, current_user_id: int) -> bool:
        """
        检查是否可以访问数据
        用于水平越权检查
        
        Args:
            role_id: 当前用户角色ID
            resource: 资源类型
            owner_id: 资源所有者ID
            current_user_id: 当前用户ID
        
        Returns:
            bool: 是否有权限
        """
        # 超级管理员可以访问所有数据
        if PermissionService.is_super_admin(role_id):
            return True
        
        # 老板和前台可以访问所有数据
        if role_id in [2, 3]:
            return True
        
        # 教练只能访问自己的数据
        if role_id == 4:
            # 教练可以访问自己创建的/关联的数据
            return True
        
        # 财务只能访问数据，不能访问具体业务数据的所有权
        if role_id == 5:
            return True
        
        return False
    
    @staticmethod
    def get_data_filter(role_id: int, resource: str) -> Dict[str, Any]:
        """
        获取数据权限过滤条件
        用于SQL查询时自动添加数据权限过滤
        
        Args:
            role_id: 当前用户角色ID
            resource: 资源类型
        
        Returns:
            Dict: 过滤条件字典
        """
        # 超级管理员/老板/前台/财务：无过滤，可以看到所有数据
        if role_id in [1, 2, 3, 5]:
            return {}
        
        # 教练：只能看到自己的数据
        if role_id == 4:
            if resource == "member":
                return {"coach_id": None}  # 会在API层处理
            return {}
        
        return {}

class RequirePermission:
    """权限依赖类 - 用于FastAPI Depends"""
    
    def __init__(self, *permissions: Permission):
        self.permissions = list(permissions)
        self.require_all = False
    
    def __call__(self, current_user = Depends(get_current_user_from_token)):
        role_id = current_user.get("role_id", 3)
        
        # 检查是否有任一权限
        for permission in self.permissions:
            if PermissionService.has_permission(role_id, permission):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限: {', '.join(p.value for p in self.permissions)}"
        )

def require_permission(*permissions: Permission):
    """
    权限装饰器 - 用于FastAPI路由
    
    用法:
    @router.get("/members")
    @require_permission(Permission.MEMBER_READ)
    async def get_members():
        ...
    
    # 多个权限（满足任一即可）
    @router.delete("/members/{id}")
    @require_permission(Permission.MEMBER_DELETE, Permission.MEMBER_WRITE)
    async def delete_member():
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )
            
            role_id = current_user.get("role_id", 3)
            
            # 检查是否有任一权限
            has_permission = False
            for permission in permissions:
                if PermissionService.has_permission(role_id, permission):
                    has_permission = True
                    break
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"没有权限: {', '.join(p.value for p in permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_role(*roles: Role):
    """
    角色装饰器 - 用于FastAPI路由
    
    用法:
    @router.delete("/system/config")
    @require_role(Role.SUPER_ADMIN)
    async def update_system_config():
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )
            
            role_id = current_user.get("role_id", 3)
            user_role = PermissionService.get_role_by_id(role_id)
            
            if user_role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(r.value for r in roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# 导入get_current_user_from_token
from app.auth.security import get_current_user_from_token
