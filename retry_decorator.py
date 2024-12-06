import time
import random
import logging
from functools import wraps
from requests.exceptions import RequestException, SSLError
from urllib3.exceptions import SSLError as BaseSSLError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries=5, base_delay=1, max_delay=32):
    """
    重试装饰器，使用指数退避策略
    :param max_retries: 最大重试次数
    :param base_delay: 基础延迟时间（秒）
    :param max_delay: 最大延迟时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (RequestException, SSLError, BaseSSLError) as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"最大重试次数已达到 ({max_retries}次). 最后一个错误: {str(e)}")
                        raise
                    
                    # 计算延迟时间（指数退避 + 随机抖动）
                    delay = min(base_delay * (2 ** (retries - 1)) + random.uniform(0, 1), max_delay)
                    logger.warning(f"请求失败 (尝试 {retries}/{max_retries}). 错误: {str(e)}")
                    logger.info(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
