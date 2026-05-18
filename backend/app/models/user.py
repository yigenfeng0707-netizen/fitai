from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    
    # 角色: 1=超级管理员, 2=店长, 3=前台, 4=教练, 5=财务
    role_id = Column(Integer, default=3)
    role_name = Column(String(50), default="前台")
    
    # 状态: active=正常, frozen=冻结, deleted=已删除
    status = Column(String(20), default="active")
    
    # 租户隔离字段
    tenant_id = Column(Integer, index=True, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # 安全字段
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User {self.username}>"

class LoginLog(Base):
    """登录日志"""
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    success = Column(Boolean, default=False)
    attempt_time = Column(DateTime, default=datetime.utcnow)
    failure_reason = Column(String(100))
    
    def __repr__(self):
        return f"<LoginLog {self.username} {self.attempt_time}>"

class AuditLog(Base):
    """操作审计日志"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String(50), index=True)
    action = Column(String(50), index=True)  # create/update/delete/login/logout
    resource = Column(String(50), index=True)  # member/course/booking/coach
    resource_id = Column(Integer)
    ip_address = Column(String(50))
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.username} {self.action} {self.resource}>"
