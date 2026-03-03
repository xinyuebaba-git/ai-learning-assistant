"""
重试机制工具

用于 API 调用、数据库操作等的自动重试
"""
import asyncio
import functools
from typing import Callable, Any, Optional, Tuple, Type
from loguru import logger


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_func: Optional[Callable[[str], None]] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        logger_func: 日志记录函数
    
    Returns:
        装饰后的函数
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if logger_func:
                        logger_func(f"尝试 {attempt}/{max_attempts} 失败：{e}")
                    else:
                        logger.warning(f"{func.__name__} 尝试 {attempt}/{max_attempts} 失败：{e}")
                    
                    if attempt < max_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if logger_func:
                        logger_func(f"尝试 {attempt}/{max_attempts} 失败：{e}")
                    else:
                        logger.warning(f"{func.__name__} 尝试 {attempt}/{max_attempts} 失败：{e}")
                    
                    if attempt < max_attempts:
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            
            raise last_exception
        
        # 判断是异步函数还是同步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 预定义的重试配置
retry_on_network_error = retry(
    max_attempts=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError, OSError)
)

retry_on_db_error = retry(
    max_attempts=3,
    delay=0.5,
    backoff=2.0,
    exceptions=(Exception,)  # SQLite 可能的并发错误
)

retry_on_llm_error = retry(
    max_attempts=2,
    delay=2.0,
    backoff=1.5,
    exceptions=(Exception,)
)
