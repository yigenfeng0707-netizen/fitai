"""
RBAC 权限系统
"""
from enum import Enum
from typing import Set


class Role(str, Enum):
    """用户角色"""
    SUPER_ADMIN = "super_admin"      # 超级管理员
    STORE_OWNER = "store_owner"      # 老板/店长
    COACH = "coach"                  # 教练
    RECEPTIONIST = "receptionist"    # 前台
    FINANCE = "finance"              # 财务


# 角色权限矩阵
ROLE_PERMISSIONS: dict[Role, Set[str]] = {
    Role.SUPER_ADMIN: {
        # 所有权限
        "member:read", "member:write", "member:delete",
        "course:read", "course:write", "course:delete",
        "booking:read", "booking:write", "booking:delete",
        "coach:read", "coach:write", "coach:delete",
        "finance:read", "finance:write", "finance:export",
        "marketing:read", "marketing:write",
        "system:read", "system:write",
        "brand:read", "brand:write",
        "audit:read",
    },
    Role.STORE_OWNER: {
        "member:read",
        "course:read",
        "booking:read",
        "coach:read",
        "finance:read",
        "marketing:read", "marketing:write",
        "system:read",
        "audit:read",
    },
    Role.COACH: {
        "member:read",  # 仅自己的学员
        "course:read",
        "booking:read", "booking:write",  # 签到
        "coach:read",  # 仅自己
        "coach:write",  # 仅自己
    },
    Role.RECEPTIONIST: {
        "member:read", "member:write",
        "course:read", "course:write",
        "booking:read", "booking:write",
        "finance:read",  # 收银
        "marketing:read", "marketing:write",
    },
    Role.FINANCE: {
        "member:read",
        "finance:read", "finance:write", "finance:export",
        "booking:read",
        "coach:read",
    },
}


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, role: Role):
        self.role = role
        self.permissions = ROLE_PERMISSIONS.get(role, set())
    
    def check(self, permission: str) -> bool:
        """检查是否有权限"""
        return permission in self.permissions
    
    def check_any(self, permissions: list[str]) -> bool:
        """检查是否有任一权限"""
        return any(p in self.permissions for p in permissions)
    
    def check_all(self, permissions: list[str]) -> bool:
        """检查是否有全部权限"""
        return all(p in self.permissions for p in permissions)


def setup_permissions():
    """初始化权限系统"""
    # 可以在这里加载自定义权限
    pass