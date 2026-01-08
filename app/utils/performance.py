import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine
from ..db.database import engine

class PerformanceMonitor:
    """Performance monitoring utility for tracking system metrics"""
    
    def __init__(self):
        self.query_times = []
        self.request_times = []
        self.system_metrics = {}
        self._setup_database_monitoring()
    
    def _setup_database_monitoring(self):
        """Setup database query monitoring"""
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            self.query_times.append(total)
            
            if total > 1.0:
                pass
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics"""
        try:
            pool = engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
            }
        except Exception as e:
            return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_total": memory.total,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "disk_total": disk.total
            }
        except Exception as e:
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.query_times:
            return {"message": "No queries recorded yet"}
        
        avg_query_time = sum(self.query_times) / len(self.query_times)
        max_query_time = max(self.query_times)
        min_query_time = min(self.query_times)
        
        slow_queries = len([t for t in self.query_times if t > 1.0])
        
        return {
            "total_queries": len(self.query_times),
            "avg_query_time": round(avg_query_time, 3),
            "max_query_time": round(max_query_time, 3),
            "min_query_time": round(min_query_time, 3),
            "slow_queries": slow_queries,
            "database_stats": self.get_database_stats(),
            "system_metrics": self.get_system_metrics()
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.query_times.clear()
        self.request_times.clear()

performance_monitor = PerformanceMonitor()

def track_request_time(func):
    """Decorator to track request processing time"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            process_time = time.time() - start_time
            performance_monitor.request_times.append(process_time)
            
            if process_time > 2.0:
                pass
            
            return result
        except Exception as e:
            process_time = time.time() - start_time
            raise
    
    return wrapper

def get_performance_summary() -> Dict[str, Any]:
    """Get a summary of current performance metrics"""
    return performance_monitor.get_performance_stats()

async def monitor_performance_async():
    """Async function to continuously monitor performance"""
    while True:
        try:
            stats = performance_monitor.get_performance_stats()
            
            if len(performance_monitor.query_times) > 0:
                avg_query = sum(performance_monitor.query_times) / len(performance_monitor.query_times)
                pass
            
            system_metrics = stats.get("system_metrics", {})
            if system_metrics.get("cpu_percent", 0) > 80:
                pass
            
            if system_metrics.get("memory_percent", 0) > 80:
                pass
            
            await asyncio.sleep(300)
            
        except Exception as e:
            await asyncio.sleep(60)
