import time
import functools

# 导入配置和我们配置好的 logger
from config.config import settings
from utils.logger import logger

def retry(max_tries=None, delay=None, backoff=2, exceptions=(Exception,)):
    """
    重试装饰器，从配置文件获取默认值。

    Args:
        max_tries: 最大尝试次数 (默认从 settings 读取)。
        delay: 初始延迟时间（秒）(默认从 settings 读取)。
        backoff: 延迟倍数。
        exceptions: 需要重试的异常类型元组。

    Returns:
        装饰器函数
    """
    # 如果未提供参数，则从 settings 获取默认值
    if max_tries is None:
        max_tries = settings.API_RETRY_TIMES
    if delay is None:
        delay = settings.API_RETRY_DELAY_SECONDS

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay
            while mtries > 0:
                try:
                    # --- 调试代码开始 ---
                    logger.debug(f"[Retry Debug] Calling {func.__name__}")
                    logger.debug(f"[Retry Debug] Received args: {args}")
                    logger.debug(f"[Retry Debug] Received kwargs: {kwargs}")
                    # --- 调试代码结束 ---
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        logger.error(
                            f"Function {func.__name__} reached max retries ({max_tries}) with error: {e}",
                            exc_info=True # 记录堆栈信息
                        )
                        raise

                    logger.warning(
                        f"Function {func.__name__} failed with {type(e).__name__}, retrying in {mdelay}s... ({mtries} retries left). Error: {e}"
                    )
                    time.sleep(mdelay)
                    mdelay *= backoff
            # 根据 Pylint 的建议，如果循环结束还没返回或抛出异常，这里理论上不应到达，但为了明确，可以抛出异常。
            # 或者，如果原始函数在循环外也可能执行，保持原样 (虽然逻辑上应该在循环内返回或 raise)
            # return func(*args, **kwargs) # 保留原逻辑，以防万一
            # 更安全的做法是明确抛出错误，表示重试用尽
            logger.critical(f"Function {func.__name__} failed after exhausting all retries.")
            raise RuntimeError(f"Function {func.__name__} failed after exhausting all retries.")

        return wrapper
    return decorator

# --- 极简调试用装饰器 ---
def simple_passthrough_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"[Simple Decorator] Calling {func.__name__}")
        logger.debug(f"[Simple Decorator] Received args: {args}")
        logger.debug(f"[Simple Decorator] Received kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"[Simple Decorator] {func.__name__} returned.")
            return result
        except Exception as e:
            logger.error(f"[Simple Decorator] {func.__name__} raised an exception: {e}", exc_info=True)
            raise
    return wrapper
# --- 结束调试用装饰器 ---

# 移除旧的 __main__ 示例 