"""
FitAI - 增强审计日志模块
Phase 5: 操作日志审计增强
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
import json

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import AuditLog as AuditLogModel
from app.auth.tenant_context import TenantContext


class AuditAction(str, Enum):
    """审计操作类型"""
    # 认证相关
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # 用户管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ENABLE = "user_enable"
    USER_DISABLE = "user_disable"
    
    # 会员管理
    MEMBER_CREATE = "member_create"
    MEMBER_UPDATE = "member_update"
    MEMBER_DELETE = "member_delete"
    MEMBER_IMPORT = "member_import"
    MEMBER_EXPORT = "member_export"
    
    # 课程管理
    COURSE_CREATE = "course_create"
    COURSE_UPDATE = "course_update"
    COURSE_DELETE = "course_delete"
    COURSE_SCHEDULE = "course_schedule"
    
    # 预约管理
    BOOKING_CREATE = "booking_create"
    BOOKING_UPDATE = "booking_update"
    BOOKING_DELETE = "booking_delete"
    BOOKING_CHECKIN = "booking_checkin"
    BOOKING_CHECKOUT = "booking_checkout"
    
    # 财务管理
    PAYMENT_CREATE = "payment_create"
    PAYMENT_REFUND = "payment_refund"
    FINANCIAL_EXPORT = "financial_export"
    
    # 系统管理
    SYSTEM_CONFIG = "system_config"
    TENANT_CREATE = "tenant_create"
    TENANT_UPDATE = "tenant_update"
    TENANT_DELETE = "tenant_delete"
    
    # 数据操作
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # 其他
    OTHER = "other"


class AuditResource(str, Enum):
    """审计资源类型"""
    USER = "user"
    MEMBER = "member"
    COURSE = "course"
    SCHEDULE = "schedule"
    BOOKING = "booking"
    COACH = "coach"
    FINANCE = "finance"
    SYSTEM = "system"
    TENANT = "tenant"
    OTHER = "other"


class AuditLevel(str, Enum):
    """审计级别"""
    INFO = "info"      # 一般信息
    WARNING = "warning" # 警告
    ERROR = "error"     # 错误
    CRITICAL = "critical" # 严重


@dataclass
class AuditEvent:
    """审计事件"""
    user_id: Optional[int]
    username: Optional[str]
    action: AuditAction
    resource: AuditResource
    resource_id: Optional[Union[int, str]]
    level: AuditLevel
    ip_address: Optional[str]
    user_agent: Optional[str]
    tenant_id: Optional[int]
    details: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["action"] = self.action.value
        data["resource"] = self.resource.value
        data["level"] = self.level.value
        return data


class AuditLogger:
    """增强审计日志记录器"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session
    
    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self._db:
            return self._db
        return SessionLocal()
    
    def log(
        self,
        action: AuditAction,
        resource: AuditResource,
        resource_id: Optional[Union[int, str]] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[int] = None,
        **details
    ) -> AuditLogModel:
        """
        记录审计日志
        
        Args:
            action: 操作类型
            resource: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            username: 用户名
            level: 审计级别
            ip_address: IP地址
            user_agent: 用户代理
            tenant_id: 租户ID
            **details: 其他详情
        """
        # 如果没有提供tenant_id，尝试从上下文中获取
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()
        
        event = AuditEvent(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            level=level,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id,
            details=details,
            created_at=datetime.utcnow()
        )
        
        return self._save_audit_log(event)
    
    def _save_audit_log(self, event: AuditEvent) -> AuditLogModel:
        """保存审计日志到数据库"""
        db = self._get_db()
        
        try:
            log_entry = AuditLogModel(
                user_id=event.user_id,
                username=event.username,
                action=event.action.value,
                resource=event.resource.value,
                resource_id=str(event.resource_id) if event.resource_id else None,
                ip_address=event.ip_address,
                details=json.dumps(event.details, ensure_ascii=False) if event.details else None,
                created_at=event.created_at
            )
            
            # 如果模型有tenant_id字段，添加它
            if hasattr(log_entry, 'tenant_id'):
                log_entry.tenant_id = event.tenant_id
            
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        finally:
            if self._db is None:
                db.close()
    
    def login_success(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """记录登录成功"""
        return self.log(
            action=AuditAction.LOGIN_SUCCESS,
            resource=AuditResource.USER,
            resource_id=user_id,
            user_id=user_id,
            username=username,
            level=AuditLevel.INFO,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id
        )
    
    def login_failure(
        self,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """记录登录失败"""
        return self.log(
            action=AuditAction.LOGIN_FAILURE,
            resource=AuditResource.USER,
            username=username,
            level=AuditLevel.WARNING,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason or "unknown"
        )
    
    def member_create(
        self,
        user_id: int,
        username: str,
        member_id: int,
        member_name: str,
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """记录创建会员"""
        return self.log(
            action=AuditAction.MEMBER_CREATE,
            resource=AuditResource.MEMBER,
            resource_id=member_id,
            user_id=user_id,
            username=username,
            level=AuditLevel.INFO,
            ip_address=ip_address,
            tenant_id=tenant_id,
            member_name=member_name
        )
    
    def data_export(
        self,
        user_id: int,
        username: str,
        resource: AuditResource,
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None,
        **details
    ):
        """记录数据导出"""
        return self.log(
            action=AuditAction.DATA_EXPORT,
            resource=resource,
            user_id=user_id,
            username=username,
            level=AuditLevel.INFO,
            ip_address=ip_address,
            tenant_id=tenant_id,
            **details
        )
    
    def system_config(
        self,
        user_id: int,
        username: str,
        config_key: str,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        tenant_id: Optional[int] = None
    ):
        """记录系统配置变更"""
        return self.log(
            action=AuditAction.SYSTEM_CONFIG,
            resource=AuditResource.SYSTEM,
            user_id=user_id,
            username=username,
            level=AuditLevel.WARNING,
            ip_address=ip_address,
            tenant_id=tenant_id,
            config_key=config_key,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None
        )


class AuditQuery:
    """审计日志查询器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def query(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: Optional[Union[AuditAction, str]] = None,
        resource: Optional[Union[AuditResource, str]] = None,
        tenant_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLogModel]:
        """
        查询审计日志
        
        Args:
            user_id: 用户ID过滤
            username: 用户名过滤
            action: 操作类型过滤
            resource: 资源类型过滤
            tenant_id: 租户ID过滤
            start_time: 开始时间
            end_time: 结束时间
            skip: 跳过数量
            limit: 返回数量
        """
        query = self.db.query(AuditLogModel)
        
        if user_id is not None:
            query = query.filter(AuditLogModel.user_id == user_id)
        
        if username is not None:
            query = query.filter(AuditLogModel.username.ilike(f"%{username}%"))
        
        if action is not None:
            action_value = action.value if isinstance(action, AuditAction) else action
            query = query.filter(AuditLogModel.action == action_value)
        
        if resource is not None:
            resource_value = resource.value if isinstance(resource, AuditResource) else resource
            query = query.filter(AuditLogModel.resource == resource_value)
        
        if tenant_id is not None:
            if hasattr(AuditLogModel, 'tenant_id'):
                query = query.filter(AuditLogModel.tenant_id == tenant_id)
        
        if start_time is not None:
            query = query.filter(AuditLogModel.created_at >= start_time)
        
        if end_time is not None:
            query = query.filter(AuditLogModel.created_at <= end_time)
        
        return query.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_id(self, log_id: int) -> Optional[AuditLogModel]:
        """根据ID获取单条日志"""
        return self.db.query(AuditLogModel).filter(AuditLogModel.id == log_id).first()


# 全局审计日志记录器
_default_logger: Optional[AuditLogger] = None


def get_audit_logger(db_session: Optional[Session] = None) -> AuditLogger:
    """获取审计日志记录器"""
    if db_session:
        return AuditLogger(db_session)
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger()
    return _default_logger
