"""
DPA项目配置管理模块
支持从环境变量和.env文件加载配置
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    url: str
    host: str = "rtx4080"
    port: int = 5432
    name: str = "dpa_dev"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    model_config = {"env_prefix": "DATABASE_", "env_file": ".env", "extra": "ignore"}


class QdrantSettings(BaseSettings):
    """Qdrant向量数据库配置"""
    url: str
    host: str = "rtx4080"
    port: int = 6333
    api_key: Optional[str] = None
    collection_name: str = "dpa_documents"
    vector_size: int = 1536
    
    model_config = {"env_prefix": "QDRANT_", "env_file": ".env", "extra": "ignore"}


class Neo4jSettings(BaseSettings):
    """Neo4j图数据库配置"""
    url: str
    host: str = "rtx4080"
    port: int = 7687
    username: str
    password: str
    database: str = "neo4j"
    
    model_config = {"env_prefix": "NEO4J_", "env_file": ".env", "extra": "ignore"}


class RedisSettings(BaseSettings):
    """Redis配置"""
    url: str
    host: str = "rtx4080"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    cache_ttl: int = 3600
    
    model_config = {"env_prefix": "REDIS_", "env_file": ".env", "extra": "ignore"}


class MinIOSettings(BaseSettings):
    """MinIO对象存储配置"""
    endpoint: str = "rtx4080:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin123"
    secure: bool = False
    bucket_name: str = "dpa-documents"
    
    model_config = {"env_prefix": "MINIO_", "env_file": ".env", "extra": "ignore"}


class AIModelSettings(BaseSettings):
    """AI模型配置"""
    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_organization: Optional[str] = None
    
    # 备选API配置
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    
    # 模型选择
    default_llm_model: str = "gpt-4o"
    default_embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072
    
    # 模型参数
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    llm_top_p: float = 0.9
    
    # LangSmith监控
    langchain_tracing_v2: bool = False
    langchain_project: str = "dpa-cognitive-v3"
    langsmith_api_key: Optional[str] = None
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class FileStorageSettings(BaseSettings):
    """文件存储配置"""
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    cache_dir: str = "./data/cache"
    max_file_size: int = 50  # MB
    allowed_file_types: List[str] = ["pdf", "txt", "md", "docx", "doc"]
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class CelerySettings(BaseSettings):
    """Celery异步任务配置"""
    broker_url: str
    result_backend: str
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "Asia/Shanghai"
    
    model_config = {"env_prefix": "CELERY_", "env_file": ".env", "extra": "ignore"}


class SecuritySettings(BaseSettings):
    """安全配置"""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    
    model_config = {"env_prefix": "JWT_", "env_file": ".env", "extra": "ignore"}


class CognitiveSettings(BaseSettings):
    """认知系统配置"""
    # 工作记忆配置
    working_memory_limit: int = 7
    attention_threshold: float = 0.5
    memory_consolidation_interval: int = 300
    
    # S2分块配置
    s2_min_chunk_size: int = 500
    s2_max_chunk_size: int = 2000
    s2_target_chunk_size: int = 1000
    s2_overlap_size: int = 200
    s2_semantic_threshold: float = 0.7
    
    # 混合检索配置
    vector_retrieval_weight: float = 0.4
    graph_retrieval_weight: float = 0.35
    memory_retrieval_weight: float = 0.25
    retrieval_top_k: int = 50
    final_results_limit: int = 20
    
    # 元认知配置
    metacognitive_enabled: bool = True
    strategy_change_threshold: float = 0.3
    performance_evaluation_interval: int = 60
    confidence_threshold: float = 0.7
    
    # 认知策略
    default_cognitive_strategy: str = "exploration"
    strategy_adaptation_enabled: bool = True
    auto_strategy_selection: bool = True
    
    # 学习配置
    active_learning_enabled: bool = True
    hypothesis_generation_enabled: bool = True
    knowledge_gap_detection: bool = True
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class MemoryBankSettings(BaseSettings):
    """记忆库配置"""
    # Memory Bank存储
    memory_bank_path: str = "./memory-bank"
    dynamic_summary_update_interval: int = 300
    max_learning_journal_entries: int = 1000
    max_hypotheses_active: int = 50
    
    # RVUE循环配置
    rvue_enabled: bool = True
    rvue_verification_threshold: float = 0.8
    rvue_update_frequency: int = 600
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class BusinessSettings(BaseSettings):
    """业务配置"""
    # 项目限制
    max_projects_per_user: int = 20
    max_documents_per_project: int = 2000
    max_questions_per_day: int = 2000
    
    # 传统分块配置（向后兼容）
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    retrieval_score_threshold: float = 0.7
    rerank_top_k: int = 5
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class MonitoringSettings(BaseSettings):
    """监控配置"""
    enable_metrics: bool = True
    metrics_port: int = 9090
    request_timeout: int = 300
    worker_concurrency: int = 4
    batch_size: int = 10
    
    model_config = {"env_file": ".env", "extra": "ignore"}


class AppSettings(BaseSettings):
    """应用主配置"""
    env: str = "development"
    debug: bool = True
    app_name: str = "DPA"
    app_version: str = "1.0.0"
    secret_key: str
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8200
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8031", "http://127.0.0.1:8031", "http://localhost:8050", "http://127.0.0.1:8050", "http://localhost:8230", "http://127.0.0.1:8230"]
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "./data/logs/dpa.log"
    log_max_size: str = "10MB"
    log_backup_count: int = 5
    
    # 开发环境配置
    reload: bool = True
    debug_sql: bool = False
    debug_redis: bool = False
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class PathSettings:
    """路径配置"""
    def __init__(self, file_storage: FileStorageSettings):
        self.upload_dir = file_storage.upload_dir
        self.processed_dir = file_storage.processed_dir
        self.cache_dir = file_storage.cache_dir
        self.memory_bank = "./memory-bank"
        self.logs_dir = "./data/logs"


class Settings:
    """统一配置管理类"""
    
    def __init__(self):
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.qdrant = QdrantSettings()
        self.neo4j = Neo4jSettings()
        self.redis = RedisSettings()
        self.minio = MinIOSettings()
        self.ai_model = AIModelSettings()
        self.file_storage = FileStorageSettings()
        self.celery = CelerySettings()
        self.security = SecuritySettings()
        self.cognitive = CognitiveSettings()
        self.memory_bank = MemoryBankSettings()
        self.business = BusinessSettings()
        self.monitoring = MonitoringSettings()
        self.paths = PathSettings(self.file_storage)
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.file_storage.upload_dir,
            self.file_storage.processed_dir,
            self.file_storage.cache_dir,
            self.memory_bank.memory_bank_path,
            os.path.dirname(self.app.log_file),
            "./data/logs",
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        return self.app.env == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app.env == "production"
    
    @property
    def debug(self) -> bool:
        return self.app.debug


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()

# 在导入时创建必要目录
settings.create_directories() 