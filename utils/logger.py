"""日志配置模块"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "DeskTopPet",
    level: int = logging.DEBUG,
    log_file: str = None,
    format_string: str = None
) -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式字符串
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 默认格式
    if format_string is None:
        format_string = "[%(asctime)s] [%(levelname)s] [%(name)s.%(module)s] %(message)s"
    
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # 输出 DEBUG 及以上级别到控制台
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(module_name: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        module_name: 模块名称
        
    Returns:
        日志记录器
    """
    if module_name:
        return logging.getLogger(f"DeskTopPet.{module_name}")
    return logging.getLogger("DeskTopPet")


# 初始化默认日志配置
def init_logging(log_dir: str = "logs"):
    """
    初始化日志系统
    
    Args:
        log_dir: 日志目录
    """
    log_file = Path(log_dir) / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    setup_logger(
        name="DeskTopPet",
        level=logging.DEBUG,
        log_file=str(log_file)
    )
    get_logger().info("日志系统初始化完成")
