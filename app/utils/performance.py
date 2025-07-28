import time
import logging
import psutil
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine
from ..database import engine

# Configure logging
logger = logging.getLogger(__name__)

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
            
            # Log slow queries
            if total > 1.0:  # Log queries taking more than 1 second
                logger.warning(f"Slow query detected: {total:.3f}s - {statement[:100]}...")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics"""
        try:
            pool = engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
                # Removed pool.invalid() as it doesn't exist in QueuePool
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
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
            logger.error(f"Error getting system metrics: {e}")
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
        logger.info("Performance statistics reset")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def track_request_time(func):
    """Decorator to track request processing time"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            process_time = time.time() - start_time
            performance_monitor.request_times.append(process_time)
            
            # Log slow requests
            if process_time > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(f"Slow request detected: {process_time:.3f}s - {func.__name__}")
            
            return result
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {process_time:.3f}s - {func.__name__} - Error: {e}")
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
            
            # Log performance summary every 5 minutes
            if len(performance_monitor.query_times) > 0:
                avg_query = sum(performance_monitor.query_times) / len(performance_monitor.query_times)
                logger.info(f"Performance Summary - Avg Query: {avg_query:.3f}s, "
                          f"Total Queries: {len(performance_monitor.query_times)}")
            
            # Check for performance issues
            system_metrics = stats.get("system_metrics", {})
            if system_metrics.get("cpu_percent", 0) > 80:
                logger.warning(f"High CPU usage detected: {system_metrics['cpu_percent']}%")
            
            if system_metrics.get("memory_percent", 0) > 80:
                logger.warning(f"High memory usage detected: {system_metrics['memory_percent']}%")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying 