"""
数据库模型 - 认证
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from backend.database_base import Base, TenantMixin
from backend.core.permissions import Role


class User(Base, TenantMixin):
    """系统用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 账号
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 角色
    role = Column(String(20), nullable=False, default=Role.RECEPTIONIST)
    
    # 关联信息
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 最后登录
    last_login_at = Column(DateTime, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    orders = relationship("Order", back_populates="operator")


class AuditLog(Base, TenantMixin):
    """操作日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)