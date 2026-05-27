"""
数据库基类 - 通用
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, declared_attr, relationship


class Base(DeclarativeBase):
    pass


class TenantMixin:
    @declared_attr
    def organization_id(cls):
        return Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    @declared_attr
    def organization(cls):
        return relationship("Organization", lazy="joined")