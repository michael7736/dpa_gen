#!/usr/bin/env python3
"""配置测试脚本"""

import os
import sys

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

print("🔍 检查环境变量:")
print(f"DATABASE_URL = {os.getenv('DATABASE_URL', 'NOT_SET')}")
print(f"QDRANT_URL = {os.getenv('QDRANT_URL', 'NOT_SET')}")

print("\n🧪 测试Pydantic Settings:")
try:
    from pydantic_settings import BaseSettings
    
    class TestConfig(BaseSettings):
        database_url: str
        
        class Config:
            env_file = ".env"
            extra = "ignore"
    
    config = TestConfig()
    print(f"✅ 配置加载成功: {config.database_url}")
    
except Exception as e:
    print(f"❌ 配置加载失败: {e}") 