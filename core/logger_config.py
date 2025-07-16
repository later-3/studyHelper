import logging
import os

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

def setup_logging():
    """配置全局日志记录器。"""
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 创建一个顶级的logger
    # 我们只配置根logger，所有子logger都会继承这个配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # 设置最低日志级别

    # 如果已经有处理器了，就不要重复添加，防止日志重复打印
    if root_logger.hasHandlers():
        return

    # 定义日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 创建一个文件处理器，将日志写入文件
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 2. 创建一个流处理器，将日志输出到控制台
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    logging.info("Logger has been configured.")

def setup_logger(name: str, level='INFO'):
    """
    设置指定名称的logger
    
    Args:
        name: logger名称
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') 或对应的整数
    
    Returns:
        配置好的logger实例
    """
    # 确保全局日志配置已设置
    setup_logging()
    
    # 获取指定名称的logger
    logger = logging.getLogger(name)
    
    # 设置日志级别
    if isinstance(level, str):
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        logger.setLevel(level_map.get(level.upper(), logging.INFO))
    else:
        # 如果level已经是整数，直接使用
        logger.setLevel(level)
    
    return logger
