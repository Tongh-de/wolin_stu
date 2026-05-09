"""
统一日志配置
将所有 print 语句替换为结构化日志
"""
import logging
import sys

# 创建根日志器
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """创建配置好的日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # 格式化
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# 各模块日志器
rag_logger = setup_logger('RAG')
agent_logger = setup_logger('Agent')
db_logger = setup_logger('Database')
app_logger = setup_logger('App')


# 便捷函数
def log_info(logger_name: str, message: str, **kwargs):
    """记录信息日志"""
    logger = logging.getLogger(logger_name)
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.info(message)


def log_error(logger_name: str, message: str, error: Exception = None, **kwargs):
    """记录错误日志"""
    logger = logging.getLogger(logger_name)
    if error:
        message = f"{message} | Error: {str(error)}"
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.error(message)


def log_debug(logger_name: str, message: str, **kwargs):
    """记录调试日志"""
    logger = logging.getLogger(logger_name)
    if kwargs:
        message = f"{message} | {kwargs}"
    logger.debug(message)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return setup_logger(name)
