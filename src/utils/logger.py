"""
日志工具模块
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..config.settings import get_settings

# 全局日志配置状态
_logging_configured = False


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_size: str = "10MB",
    backup_count: int = 5
) -> None:
    """设置日志配置"""
    global _logging_configured
    
    if _logging_configured:
        return
    
    settings = get_settings()
    
    # 使用配置或默认值
    level = log_level or settings.app.log_level
    file_path = log_file or settings.app.log_file
    format_string = log_format or settings.app.log_format
    
    # 解析日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建日志目录
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建格式化器
    formatter = logging.Formatter(format_string)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了文件路径）
    if file_path:
        try:
            # 解析文件大小
            size_bytes = _parse_size(max_size)
            
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=size_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # 如果文件处理器创建失败，只使用控制台输出
            console_handler.warning(f"无法创建文件日志处理器: {e}")
    
    # 设置第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    _logging_configured = True


def _parse_size(size_str: str) -> int:
    """解析大小字符串为字节数"""
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # 假设是字节数
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    # 确保日志已配置
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


class ContextLogger:
    """带上下文的日志器"""
    
    def __init__(self, logger: logging.Logger, context: dict):
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """格式化消息，添加上下文信息"""
        context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
        return f"[{context_str}] {message}"
    
    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(self._format_message(message), *args, **kwargs)


def get_context_logger(name: str, **context) -> ContextLogger:
    """获取带上下文的日志器"""
    logger = get_logger(name)
    return ContextLogger(logger, context) 