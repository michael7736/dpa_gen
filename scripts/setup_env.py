#!/usr/bin/env python3
"""
DPA认知系统环境配置脚本
帮助用户快速设置必要的环境变量
"""

import os
import sys
from pathlib import Path
import secrets

def create_env_file():
    """创建.env文件"""
    env_path = Path(".env")
    
    if env_path.exists():
        response = input(".env文件已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("配置取消")
            return False
    
    print("🚀 开始配置DPA认知系统环境...")
    
    # 获取OpenAI API密钥
    openai_api_key = input("\n请输入你的OpenAI API密钥: ").strip()
    if not openai_api_key:
        print("❌ OpenAI API密钥是必需的！")
        return False
    
    # 生成安全密钥
    secret_key = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)
    
    # 询问数据库配置
    print("\n📊 数据库配置:")
    print("1. 使用本地SQLite (推荐，简单)")
    print("2. 使用PostgreSQL")
    db_choice = input("选择数据库类型 (1/2) [1]: ").strip() or "1"
    
    if db_choice == "2":
        db_host = input("PostgreSQL主机 [localhost]: ").strip() or "localhost"
        db_port = input("PostgreSQL端口 [5432]: ").strip() or "5432"
        db_name = input("数据库名 [dpa_cognitive]: ").strip() or "dpa_cognitive"
        db_user = input("用户名 [postgres]: ").strip() or "postgres"
        db_password = input("密码: ").strip()
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        database_url = "sqlite:///./data/dpa_cognitive.db"
    
    # 询问向量数据库配置
    print("\n🔍 向量数据库配置:")
    use_qdrant = input("是否使用本地Qdrant？(Y/n) [Y]: ").strip().lower()
    if use_qdrant in ['', 'y', 'yes']:
        qdrant_url = input("Qdrant地址 [http://localhost:6333]: ").strip() or "http://localhost:6333"
    else:
        qdrant_url = "memory://local"
    
    # 询问图数据库配置
    print("\n🕸️ 图数据库配置:")
    use_neo4j = input("是否使用本地Neo4j？(Y/n) [Y]: ").strip().lower()
    if use_neo4j in ['', 'y', 'yes']:
        neo4j_url = input("Neo4j地址 [bolt://localhost:7687]: ").strip() or "bolt://localhost:7687"
        neo4j_user = input("Neo4j用户名 [neo4j]: ").strip() or "neo4j"
        neo4j_password = input("Neo4j密码: ").strip()
    else:
        neo4j_url = "memory://local"
        neo4j_user = "neo4j"
        neo4j_password = "password"
    
    # 询问Redis配置
    print("\n⚡ Redis配置:")
    use_redis = input("是否使用本地Redis？(Y/n) [Y]: ").strip().lower()
    if use_redis in ['', 'y', 'yes']:
        redis_url = input("Redis地址 [redis://localhost:6379]: ").strip() or "redis://localhost:6379"
    else:
        redis_url = "memory://local"
    
    # 生成.env文件内容
    env_content = f"""# DPA认知系统环境配置
# 生成时间: {os.popen('date').read().strip()}

# ==========================================
# API配置
# ==========================================
OPENAI_API_KEY={openai_api_key}

# 应用安全配置
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}

# ==========================================
# 数据库配置
# ==========================================
DATABASE_URL={database_url}

# ==========================================
# 向量数据库配置
# ==========================================
QDRANT_URL={qdrant_url}

# ==========================================
# 图数据库配置
# ==========================================
NEO4J_URL={neo4j_url}
NEO4J_USERNAME={neo4j_user}
NEO4J_PASSWORD={neo4j_password}

# ==========================================
# Redis配置
# ==========================================
REDIS_URL={redis_url}

# Celery配置
CELERY_BROKER_URL={redis_url}/1
CELERY_RESULT_BACKEND={redis_url}/2

# ==========================================
# 应用配置
# ==========================================
ENV=development
DEBUG=True
LOG_LEVEL=INFO
RELOAD=True

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# ==========================================
# 认知系统配置
# ==========================================
# 工作记忆配置
WORKING_MEMORY_LIMIT=7
ATTENTION_THRESHOLD=0.5

# S2语义分块配置
S2_MIN_CHUNK_SIZE=500
S2_MAX_CHUNK_SIZE=2000
S2_TARGET_CHUNK_SIZE=1000
S2_OVERLAP_SIZE=200
S2_SEMANTIC_THRESHOLD=0.7

# 混合检索配置
VECTOR_RETRIEVAL_WEIGHT=0.4
GRAPH_RETRIEVAL_WEIGHT=0.35
MEMORY_RETRIEVAL_WEIGHT=0.25
RETRIEVAL_TOP_K=50
FINAL_RESULTS_LIMIT=20

# 元认知配置
METACOGNITIVE_ENABLED=True
STRATEGY_CHANGE_THRESHOLD=0.3
CONFIDENCE_THRESHOLD=0.7

# 记忆库配置
MEMORY_BANK_PATH=./memory-bank
RVUE_ENABLED=True

# ==========================================
# 业务配置
# ==========================================
MAX_PROJECTS_PER_USER=20
MAX_DOCUMENTS_PER_PROJECT=2000
MAX_QUESTIONS_PER_DAY=2000

# ==========================================
# 监控配置
# ==========================================
ENABLE_METRICS=True
LANGCHAIN_TRACING_V2=false
"""
    
    # 写入文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ 环境配置文件已创建: {env_path.absolute()}")
    
    # 创建必要目录
    directories = [
        "data/uploads",
        "data/processed", 
        "data/cache",
        "data/logs",
        "memory-bank"
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
    
    print("✅ 必要目录已创建")
    
    return True


def test_configuration():
    """测试配置是否正确"""
    print("\n🧪 测试配置...")
    
    try:
        # 添加项目根目录到Python路径
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from src.config.settings import get_settings
        settings = get_settings()
        
        print("✅ 配置加载成功")
        
        # 测试OpenAI API密钥
        if settings.ai_model.openai_api_key:
            print("✅ OpenAI API密钥已配置")
        else:
            print("❌ OpenAI API密钥未配置")
            return False
        
        # 测试目录
        if Path("data").exists():
            print("✅ 数据目录存在")
        
        if Path("memory-bank").exists():
            print("✅ 记忆库目录存在")
        
        print("\n🎉 配置测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🧠 DPA认知系统环境配置向导")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("src").exists():
        print("❌ 请在DPA项目根目录运行此脚本")
        sys.exit(1)
    
    # 创建环境配置
    if create_env_file():
        print("\n" + "=" * 50)
        
        # 测试配置
        if test_configuration():
            print("\n🚀 恭喜！DPA认知系统环境配置完成")
            print("\n下一步:")
            print("1. 运行测试: python tests/test_complete_cognitive_system.py")
            print("2. 启动API服务: uvicorn src.api.main:app --reload")
            print("3. 查看文档: http://localhost:8000/docs")
        else:
            print("\n⚠️ 配置完成但测试失败，请检查配置")
    else:
        print("\n❌ 环境配置失败")
        sys.exit(1)


if __name__ == "__main__":
    main()