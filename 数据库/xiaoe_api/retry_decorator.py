"""
重试机制装饰器
"""
import time
import functools
from loguru import logger

def retry(max_tries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    重试装饰器
    
    Args:
        max_tries: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        logger.error(f"函数 {func.__name__} 已达到最大重试次数 ({max_tries}): {e}")
                        raise
                    
                    logger.warning(f"函数 {func.__name__} 发生异常，{mdelay}秒后重试 (剩余尝试: {mtries}): {e}")
                    time.sleep(mdelay)
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    @retry(max_tries=3, delay=1, backoff=2, exceptions=(ValueError, TypeError))
    def example_function(x):
        if x < 0:
            raise ValueError("Value must be positive")
        if x > 100:
            raise TypeError("Value too large")
        return x * 2
    
    try:
        # 会失败并重试3次
        result = example_function(-1)
    except ValueError:
        print("捕获到最终的ValueError异常")
    
    # 正常调用会成功
    result = example_function(10)
    print(f"结果: {result}") 