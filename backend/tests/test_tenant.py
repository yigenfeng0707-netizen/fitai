"""
FitAI - Phase 3 测试
测试多租户数据隔离
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.member import Member
from app.models.course import Course
from app.models.tenant import Tenant
from app.auth.tenant_context import TenantContext
from app.auth.permission_middleware import DataPermissionFilter


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestTenantModel:
    """租户模型测试"""
    
    def test_create_tenant(self, db_session):
        """测试创建租户"""
        tenant = Tenant(
            tenant_name="测试健身房",
            tenant_code="test_gym",
            domain="test-gym.example.com",
            max_users=10,
            max_members=100,
            is_active=True
        )
        db_session.add(tenant)
        db_session.commit()
        
        assert tenant.id is not None
        assert tenant.tenant_name == "测试健身房"
        assert tenant.tenant_code == "test_gym"
        assert tenant.is_active is True
    
    def test_tenant_code_unique(self, db_session):
        """测试租户编码唯一性"""
        tenant1 = Tenant(tenant_name="租户1", tenant_code="gym1")
        tenant2 = Tenant(tenant_name="租户2", tenant_code="gym1")
        
        db_session.add(tenant1)
        db_session.commit()
        
        with pytest.raises(Exception):
            db_session.add(tenant2)
            db_session.commit()


class TestTenantContext:
    """租户上下文测试"""
    
    def test_set_and_get_tenant(self):
        """测试设置和获取租户"""
        TenantContext.set_tenant(1, "gym1")
        
        assert TenantContext.get_tenant_id() == 1
        assert TenantContext.get_tenant_code() == "gym1"
        assert TenantContext.has_tenant() is True
    
    def test_clear_tenant(self):
        """测试清除租户"""
        TenantContext.set_tenant(1, "gym1")
        TenantContext.clear()
        
        assert TenantContext.get_tenant_id() is None
        assert TenantContext.get_tenant_code() is None
        assert TenantContext.has_tenant() is False


class TestTenantIsolation:
    """租户隔离测试"""
    
    def setup_method(self):
        """每个测试前重置租户上下文"""
        TenantContext.clear()
    
    def test_member_tenant_isolation(self, db_session):
        """测试会员数据租户隔离"""
        # 创建两个租户
        tenant1 = Tenant(tenant_name="租户1", tenant_code="gym1")
        tenant2 = Tenant(tenant_name="租户2", tenant_code="gym2")
        db_session.add_all([tenant1, tenant2])
        db_session.commit()
        
        # 为每个租户创建会员
        member1 = Member(
            member_no="M001",
            name="会员1",
            phone="13800138001",
            tenant_id=tenant1.id
        )
        member2 = Member(
            member_no="M002",
            name="会员2",
            phone="13800138002",
            tenant_id=tenant2.id
        )
        db_session.add_all([member1, member2])
        db_session.commit()
        
        # 设置租户1上下文
        TenantContext.set_tenant(tenant1.id, tenant1.tenant_code)
        
        # 查询会员，应该只看到租户1的会员
        query = db_session.query(Member)
        filtered_query = DataPermissionFilter.apply_tenant_filter(query, Member)
        result = filtered_query.all()
        
        assert len(result) == 1
        assert result[0].name == "会员1"
        assert result[0].tenant_id == tenant1.id
        
        # 切换到租户2
        TenantContext.set_tenant(tenant2.id, tenant2.tenant_code)
        
        query = db_session.query(Member)
        filtered_query = DataPermissionFilter.apply_tenant_filter(query, Member)
        result = filtered_query.all()
        
        assert len(result) == 1
        assert result[0].name == "会员2"
        assert result[0].tenant_id == tenant2.id
    
    def test_super_admin_can_see_all(self, db_session):
        """测试超级管理员可以看到所有数据"""
        # 创建两个租户
        tenant1 = Tenant(tenant_name="租户1", tenant_code="gym1")
        tenant2 = Tenant(tenant_name="租户2", tenant_code="gym2")
        db_session.add_all([tenant1, tenant2])
        db_session.commit()
        
        # 为每个租户创建会员
        member1 = Member(
            member_no="M001",
            name="会员1",
            phone="13800138001",
            tenant_id=tenant1.id
        )
        member2 = Member(
            member_no="M002",
            name="会员2",
            phone="13800138002",
            tenant_id=tenant2.id
        )
        db_session.add_all([member1, member2])
        db_session.commit()
        
        # 超级管理员（tenant_id为None）
        TenantContext.set_tenant(None, None)
        
        query = db_session.query(Member)
        filtered_query = DataPermissionFilter.apply_tenant_filter(query, Member)
        result = filtered_query.all()
        
        assert len(result) == 2
    
    def test_course_tenant_isolation(self, db_session):
        """测试课程数据租户隔离"""
        tenant1 = Tenant(tenant_name="租户1", tenant_code="gym1")
        tenant2 = Tenant(tenant_name="租户2", tenant_code="gym2")
        db_session.add_all([tenant1, tenant2])
        db_session.commit()
        
        course1 = Course(
            name="瑜伽课",
            course_type="group",
            duration=60,
            price=100.0,
            tenant_id=tenant1.id
        )
        course2 = Course(
            name="私教课",
            course_type="private",
            duration=60,
            price=300.0,
            tenant_id=tenant2.id
        )
        db_session.add_all([course1, course2])
        db_session.commit()
        
        TenantContext.set_tenant(tenant1.id, tenant1.tenant_code)
        
        query = db_session.query(Course)
        filtered_query = DataPermissionFilter.apply_tenant_filter(query, Course)
        result = filtered_query.all()
        
        assert len(result) == 1
        assert result[0].name == "瑜伽课"


class TestTenantCRUD:
    """租户CRUD测试"""
    
    def test_create_tenant(self, db_session):
        """测试创建租户"""
        from app.crud.tenant import TenantCRUD
        
        tenant = TenantCRUD.create_tenant(
            db=db_session,
            tenant_name="测试健身房",
            tenant_code="test_gym_001",
            max_users=20,
            max_members=500
        )
        
        assert tenant.id is not None
        assert tenant.tenant_name == "测试健身房"
        assert tenant.max_users == 20
        assert tenant.max_members == 500
    
    def test_get_tenant_by_code(self, db_session):
        """测试根据编码获取租户"""
        from app.crud.tenant import TenantCRUD
        
        TenantCRUD.create_tenant(
            db=db_session,
            tenant_name="测试健身房",
            tenant_code="test_gym_002"
        )
        
        tenant = TenantCRUD.get_tenant_by_code(db_session, "test_gym_002")
        assert tenant is not None
        assert tenant.tenant_name == "测试健身房"
    
    def test_deactivate_tenant(self, db_session):
        """测试停用租户"""
        from app.crud.tenant import TenantCRUD
        
        tenant = TenantCRUD.create_tenant(
            db=db_session,
            tenant_name="测试健身房",
            tenant_code="test_gym_003"
        )
        
        assert tenant.is_active is True
        
        deactivated = TenantCRUD.deactivate_tenant(db_session, tenant.id)
        assert deactivated is not None
        assert deactivated.is_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
