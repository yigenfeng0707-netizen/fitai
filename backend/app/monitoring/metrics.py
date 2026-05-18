"""
FitAI - 指标收集模块
Phase 6: 监控告警集成
"""
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import threading
import time


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._timers: Dict[str, float] = {}
        self._lock = threading.Lock()
        
    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """增加计数器"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
            
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """设置仪表盘"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
            
    def record_duration(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """记录持续时间"""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(duration)
            
    def start_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """开始计时"""
        timer_id = f"{name}_{time.time()}"
        self._timers[timer_id] = time.time()
        return timer_id
        
    def stop_timer(self, timer_id: str) -> Optional[float]:
        """停止计时并记录"""
        if timer_id not in self._timers:
            return None
            
        start_time = self._timers.pop(timer_id)
        duration = time.time() - start_time
        
        # 从timer_id中提取原始名称
        name = timer_id.rsplit('_', 1)[0]
        self.record_duration(name, duration)
        return duration
        
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    k: {
                        'count': len(v),
                        'sum': sum(v),
                        'avg': sum(v)/len(v) if v else 0,
                        'min': min(v) if v else 0,
                        'max': max(v) if v else 0
                    }
                    for k, v in self._histograms.items()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'


# 全局实例
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
