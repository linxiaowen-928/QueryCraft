"""
性能监控和指标收集
用于实时监控系统性能
"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from collections import defaultdict, deque
import threading 
import logging


logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        # API 调用指标
        self.api_calls: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.errors: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.concurrent_requests = 0
        self.max_concurrent_requests = 0
        
        # 数据库指标
        self.db_queries: deque = deque(maxlen=1000)
        
        # LLM 指标
        self.llm_calls: deque = deque(maxlen=1000) 
        
        # Cache 指标
        self.cache_hits = 0
        self.cache_misses = 0
        
        self._lock = threading.Lock()
    
    def record_api_call(self, endpoint: str, duration_ms: float, success: bool = True):
        """记录API调用"""
        with self._lock:
            self.api_calls[endpoint].append({
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                'success': success
            })
            
            if not success:
                self.errors[endpoint].append(datetime.now())
    
    def record_db_query(self, duration_ms: float, success: bool = True):
        """记录数据库查询"""
        with self._lock:
            self.db_queries.append({
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                'success': success
            })
    
    def record_llm_call(self, duration_ms: float, success: bool = True):
        """记录LLM API调用"""
        with self._lock:
            self.llm_calls.append({
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                'success': success
            })
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self._lock:
            self.cache_hits += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self._lock:
            self.cache_misses += 1
            
    def track_concurrent_requests(self, increment: int):
        """跟踪并发请求数"""
        with self._lock:
            self.concurrent_requests += increment
            self.max_concurrent_requests = max(
                self.max_concurrent_requests,
                self.concurrent_requests
            )
    
    def get_api_metrics(self, endpoint: str = None, timeframe_hours: int = 1) -> Dict:
        """获取API指标"""
        cutoff = datetime.now() - timedelta(hours=timeframe_hours)
        
        if endpoint:
            calls = [c for c in self.api_calls[endpoint] if c['timestamp'] >= cutoff]
            errors = [e for e in self.errors[endpoint] if e >= cutoff]
        else:
            calls = []
            errors = []
            for call_list in self.api_calls.values():
                calls.extend([c for c in call_list if c['timestamp'] >= cutoff])
            for error_list in self.errors.values():
                errors.extend([e for e in error_list if e >= cutoff])
        
        if not calls:
            return {'error': 'No data available'}
        
        durations = [c['duration_ms'] for c in calls]
        success_count = sum(1 for c in calls if c['success'])
        error_count = len(errors)
        total_count = len(calls)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        p95_duration = sorted(durations)[int(0.95 * len(durations))] if durations else 0
        
        return {
            'total_calls': total_count,
            'successful_calls': success_count,
            'failed_calls': error_count,
            'success_rate_percent': round(success_count / total_count * 100, 2),
            'average_duration_ms': round(avg_duration, 2),
            'p95_duration_ms': round(p95_duration, 2),
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
        }
    
    def get_cache_metrics(self) -> Dict:
        """获取缓存指标"""
        total_accesses = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_accesses * 100) if total_accesses > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_total_accesses': total_accesses,
            'cache_hit_rate_percent': round(hit_rate, 2)
        }
    
    def get_db_metrics(self, timeframe_hours: int = 1) -> Dict:
        """获取数据库指标"""
        cutoff = datetime.now() - timedelta(hours=timeframe_hours)
        queries = [q for q in self.db_queries if q['timestamp'] >= cutoff]
        
        if not queries:
            return {'error': 'No data available'}
        
        durations = [q['duration_ms'] for q in queries]
        success_count = sum(1 for q in queries if q['success'])
        total_count = len(queries)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        p95_duration = sorted(durations)[int(0.95 * len(durations))] if durations else 0
        
        return {
            'total_queries': total_count,
            'successful_queries': success_count,
            'average_duration_ms': round(avg_duration, 2),
            'p95_duration_ms': round(p95_duration, 2),
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
        }
    
    def get_overall_stats(self) -> Dict:
        """获取总体统计数据"""
        return {
            'peak_concurrent_requests': self.max_concurrent_requests,
            'current_concurrent_requests': self.concurrent_requests,
            'cache_metrics': self.get_cache_metrics()
        }


# 全局性能指标实例
perf_metrics = PerformanceMetrics()


class PerformanceMonitor:
    """性能监控器装饰器"""
    
    def __init__(self, endpoint_name: str = None):
        self.endpoint_name = endpoint_name or "unknown"
    
    def __call__(self, func):
        """装饰器实现"""
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            perf_metrics.track_concurrent_requests(1)
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功的API调用
                duration_ms = (time.time() - start_time) * 1000
                perf_metrics.record_api_call(
                    self.endpoint_name, 
                    duration_ms, 
                    success=True
                )
                return result
            except Exception as e:
                # 记录失败的API调用
                duration_ms = (time.time() - start_time) * 1000
                perf_metrics.record_api_call(
                    self.endpoint_name, 
                    duration_ms, 
                    success=False
                )
                raise e
            finally:
                perf_metrics.track_concurrent_requests(-1)
        
        return wrapper


def monitor_db_query(func):
    """监控数据库查询的装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # 记录成功的查询
            duration_ms = (time.time() - start_time) * 1000
            perf_metrics.record_db_query(duration_ms, success=True)
            return result
        except Exception as e:
            # 记录失败的查询
            duration_ms = (time.time() - start_time) * 1000
            perf_metrics.record_db_query(duration_ms, success=False)
            raise e
    
    return wrapper


def monitor_llm_call(func):
    """监控LLM API调用的装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # 记录成功的LLM调用
            duration_ms = (time.time() - start_time) * 1000
            perf_metrics.record_llm_call(duration_ms, success=True)
            return result
        except Exception as e:
            # 记录失败的LLM调用
            duration_ms = (time.time() - start_time) * 1000
            perf_metrics.record_llm_call(duration_ms, success=False)  
            raise e
    
    return wrapper