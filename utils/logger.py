"""
日志配置模块
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 日志目录
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def setup_logger(name: str, log_file: str = None, level: str = None) -> logging.Logger:
    """
    创建并配置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别（可选，默认使用全局设置）

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, (level or LOG_LEVEL).upper()))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt=DATE_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# 全局应用日志记录器
app_logger = setup_logger("app", os.path.join(LOG_DIR, "app.log"))


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 模块名称

    Returns:
        日志记录器
    """
    log_files = {
        "student": "students.log",
        "class": "classes.log",
        "teacher": "teachers.log",
        "exam": "exams.log",
        "employment": "employment.log",
        "auth": "auth.log",
        "query": "query.log",
        "statistics": "statistics.log",
    }

    log_file = log_files.get(name.lower())
    if log_file:
        log_path = os.path.join(LOG_DIR, log_file)
        return setup_logger(name, log_path)

    return setup_logger(name)
