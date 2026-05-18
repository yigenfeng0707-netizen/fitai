"""
FitAI - 熔断器模块
Phase 8: 异常容错与熔断
"""
from enum import Enum
from typing import Callable, Optional, Any
from functools import wraps
import time
import threading


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: tuple = (Exception,)
        name: Optional[str] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "circuit_breaker"
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """调用函数，带熔断保护"""
        self._check_state()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
            
    def _check_state(self):
        """检查当前状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit '{self.name}' is open"
                    )
                    
    def _on_success(self):
        """成功时的处理"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
                
    def _on_failure(self):
        """失败时的处理"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            return self._state
            
    @property
    def failure_count(self) -> int:
        """获取失败计数"""
        with self._lock:
            return self._failure_count
            
    def reset(self):
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0


class CircuitBreakerOpenException(Exception):
    """熔断器打开异常"""
    pass


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exception: tuple = (Exception,)
):
    """熔断器装饰器"""
    def decorator(func: Callable) -> Callable:
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=func.__name__
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return cb.call(func, *args, **kwargs)
            
        # 暴露熔断器实例
        wrapper.circuit_breaker = cb
        
        return wrapper
        
    return decorator
