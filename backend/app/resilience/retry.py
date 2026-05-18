"""
FitAI - 重试模块
Phase 8: 异常容错与熔断
"""
from typing import Callable, Optional, Any, Tuple
from functools import wraps
import time
import random


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    exceptions: Tuple[type, ...] = (Exception,)
):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                        
                    # 计算延迟，加入抖动
                    jitter_amount = current_delay * jitter * (2 * random.random() - 1)
                    sleep_time = current_delay + jitter_amount
                    
                    time.sleep(max(0, sleep_time))
                    current_delay *= backoff
                    
            raise last_exception
            
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: float = 0.1,
    exceptions: Tuple[type, ...] = (Exception,)
):
    """异步重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                        
                    # 计算延迟，加入抖动
                    jitter_amount = current_delay * jitter * (2 * random.random() - 1)
                    sleep_time = current_delay + jitter_amount
                    
                    import asyncio
                    await asyncio.sleep(max(0, sleep_time))
                    current_delay *= backoff
                    
            raise last_exception
            
        return wrapper
    return decorator
