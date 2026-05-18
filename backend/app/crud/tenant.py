from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.models.tenant import Tenant


class TenantCRUD:
    """租户CRUD操作"""
    
    @staticmethod
    def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
        """根据ID获取租户"""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    @staticmethod
    def get_tenant_by_code(db: Session, tenant_code: str) -> Optional[Tenant]:
        """根据编码获取租户"""
        return db.query(Tenant).filter(Tenant.tenant_code == tenant_code).first()
    
    @staticmethod
    def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """获取所有租户"""
        return db.query(Tenant).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_tenant(
        db: Session,
        tenant_name: str,
        tenant_code: str,
        domain: Optional[str] = None,
        description: Optional[str] = None,
        max_users: int = 100,
        max_members: int = 10000,
        max_storage: int = 10240,
        subscription_plan: str = "basic",
        subscription_days: int = 365
    ) -> Tenant:
        """创建租户"""
        tenant = Tenant(
            tenant_name=tenant_name,
            tenant_code=tenant_code,
            domain=domain,
            description=description,
            max_users=max_users,
            max_members=max_members,
            max_storage=max_storage,
            subscription_plan=subscription_plan,
            subscription_start=datetime.utcnow(),
            subscription_end=datetime.utcnow() + timedelta(days=subscription_days),
            is_active=True
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
    
    @staticmethod
    def update_tenant(
        db: Session,
        tenant_id: int,
        **kwargs
    ) -> Optional[Tenant]:
        """更新租户"""
        tenant = TenantCRUD.get_tenant(db, tenant_id)
        if not tenant:
            return None
        
        for key, value in kwargs.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tenant)
        return tenant
    
    @staticmethod
    def activate_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
        """激活租户"""
        return TenantCRUD.update_tenant(db, tenant_id, is_active=True)
    
    @staticmethod
    def deactivate_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
        """停用租户"""
        return TenantCRUD.update_tenant(db, tenant_id, is_active=False)
    
    @staticmethod
    def delete_tenant(db: Session, tenant_id: int) -> bool:
        """删除租户（软删除）"""
        tenant = TenantCRUD.get_tenant(db, tenant_id)
        if not tenant:
            return False
        
        tenant.is_active = False
        tenant.updated_at = datetime.utcnow()
        db.commit()
        return True
