"""
环境配置管理器
支持多环境配置和配置继承
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import re

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self, environment: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            environment: 环境名称 (development, testing, production)
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config_dir = Path("config/environments")
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 1. 加载基础配置
        base_config = self._load_yaml_file("base.yml")
        if base_config:
            self._config = base_config
        
        # 2. 加载环境特定配置并合并
        env_config = self._load_yaml_file(f"{self.environment}.yml")
        if env_config:
            self._config = self._deep_merge(self._config, env_config)
        
        # 3. 处理环境变量替换
        self._substitute_env_vars()
        
        # 4. 验证必需配置
        self._validate_config()
        
        logger.info(f"Loaded configuration for environment: {self.environment}")
    
    def _load_yaml_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """加载YAML文件"""
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Configuration file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration file {filepath}: {e}")
            return None
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _substitute_env_vars(self):
        """替换配置中的环境变量"""
        def substitute(obj):
            if isinstance(obj, str):
                # 匹配 ${VAR_NAME} 格式
                pattern = r'\$\{([^}]+)\}'
                
                def replacer(match):
                    var_name = match.group(1)
                    value = os.getenv(var_name)
                    if value is None:
                        logger.warning(f"Environment variable not found: {var_name}")
                        return match.group(0)  # 保持原样
                    return value
                
                return re.sub(pattern, replacer, obj)
            elif isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            else:
                return obj
        
        self._config = substitute(self._config)
    
    def _validate_config(self):
        """验证必需的配置项"""
        required_keys = [
            "environment",
            "database.postgresql.host",
            "database.qdrant.host",
            "api.prefix",
        ]
        
        for key in required_keys:
            if not self.get(key):
                raise ValueError(f"Required configuration missing: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径 (e.g., "database.postgresql.host")
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_url(self, db_type: str = "postgresql") -> str:
        """获取数据库连接URL"""
        if db_type == "postgresql":
            config = self.get("database.postgresql", {})
            username = config.get("username", "postgres")
            password = config.get("password", "postgres")
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            database = config.get("database", "dpa")
            
            return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        
        elif db_type == "redis":
            config = self.get("database.redis", {})
            password = config.get("password")
            host = config.get("host", "localhost")
            port = config.get("port", 6379)
            db = config.get("db", 0)
            
            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            else:
                return f"redis://{host}:{port}/{db}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """获取功能开关配置"""
        return self.get("feature_flags", {})
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == "testing"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.get(key) is not None


# 全局配置实例（单例模式）
@lru_cache(maxsize=1)
def get_environment_config() -> EnvironmentConfig:
    """获取环境配置实例"""
    return EnvironmentConfig()


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return get_environment_config().get(key, default)


def get_database_url(db_type: str = "postgresql") -> str:
    """获取数据库URL的便捷函数"""
    return get_environment_config().get_database_url(db_type)


def is_feature_enabled(feature_name: str) -> bool:
    """检查功能是否启用的便捷函数"""
    flags = get_environment_config().get_feature_flags()
    return flags.get(feature_name, False)


# 配置验证器
class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_database_config(config: EnvironmentConfig) -> bool:
        """验证数据库配置"""
        try:
            # PostgreSQL
            pg_config = config.get("database.postgresql", {})
            assert pg_config.get("host"), "PostgreSQL host is required"
            assert pg_config.get("port"), "PostgreSQL port is required"
            assert pg_config.get("database"), "PostgreSQL database is required"
            
            # Qdrant
            qdrant_config = config.get("database.qdrant", {})
            assert qdrant_config.get("host"), "Qdrant host is required"
            assert qdrant_config.get("port"), "Qdrant port is required"
            
            # Redis
            redis_config = config.get("database.redis", {})
            assert redis_config.get("host"), "Redis host is required"
            assert redis_config.get("port"), "Redis port is required"
            
            return True
        except AssertionError as e:
            logger.error(f"Database configuration validation failed: {e}")
            return False
    
    @staticmethod
    def validate_api_config(config: EnvironmentConfig) -> bool:
        """验证API配置"""
        try:
            api_config = config.get("api", {})
            assert api_config.get("prefix"), "API prefix is required"
            
            server_config = config.get("server", {})
            assert server_config.get("host"), "Server host is required"
            assert server_config.get("port"), "Server port is required"
            
            return True
        except AssertionError as e:
            logger.error(f"API configuration validation failed: {e}")
            return False
    
    @staticmethod
    def validate_all(config: EnvironmentConfig) -> bool:
        """验证所有配置"""
        validators = [
            ConfigValidator.validate_database_config,
            ConfigValidator.validate_api_config,
        ]
        
        return all(validator(config) for validator in validators)