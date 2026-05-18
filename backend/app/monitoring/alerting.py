"""
FitAI - 告警管理模块
Phase 6: 监控告警集成
"""
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
import threading


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警数据类"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    labels: Dict[str, str]
    created_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
        
    def alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "system",
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """发送告警"""
        alert_id = f"alert_{datetime.utcnow().timestamp()}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            labels=labels or {},
            created_at=datetime.utcnow()
        )
        
        with self._lock:
            self._alerts[alert_id] = alert
        
        # 触发处理器
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception:
                pass  # 处理器异常不影响主流程
                
        return alert_id
        
    def resolve(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                self._alerts[alert_id].resolved_at = datetime.utcnow()
                return True
        return False
        
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """获取告警列表"""
        with self._lock:
            alerts = list(self._alerts.values())
            
        # 过滤
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
            
        # 排序和限制
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        return alerts[:limit]
        
    def add_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self._handlers.append(handler)
        
    def info(self, title: str, message: str, **kwargs) -> str:
        """信息级别告警"""
        return self.alert(AlertLevel.INFO, title, message, **kwargs)
        
    def warning(self, title: str, message: str, **kwargs) -> str:
        """警告级别告警"""
        return self.alert(AlertLevel.WARNING, title, message, **kwargs)
        
    def error(self, title: str, message: str, **kwargs) -> str:
        """错误级别告警"""
        return self.alert(AlertLevel.ERROR, title, message, **kwargs)
        
    def critical(self, title: str, message: str, **kwargs) -> str:
        """严重级别告警"""
        return self.alert(AlertLevel.CRITICAL, title, message, **kwargs)


# 全局实例
_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _manager
    if _manager is None:
        _manager = AlertManager()
    return _manager
