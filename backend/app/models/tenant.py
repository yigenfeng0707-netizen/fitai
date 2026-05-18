from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Tenant(Base):
    """租户模型"""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_name = Column(String(100), nullable=False)  # 租户名称
    tenant_code = Column(String(50), unique=True, index=True, nullable=False)  # 租户编码
    domain = Column(String(100))  # 租户域名
    description = Column(Text)  # 描述
    max_users = Column(Integer, default=100)  # 最大用户数
    max_members = Column(Integer, default=10000)  # 最大会员数
    max_storage = Column(Integer, default=10240)  # 最大存储空间(MB)
    is_active = Column(Boolean, default=True)  # 是否激活
    subscription_plan = Column(String(50), default="basic")  # 订阅套餐
    subscription_start = Column(DateTime)  # 订阅开始时间
    subscription_end = Column(DateTime)  # 订阅结束时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tenant {self.tenant_name}>"
