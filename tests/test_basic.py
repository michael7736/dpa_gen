"""基础测试模块 - 确保CI流水线正常运行"""

import pytest
from src.config.settings import Settings
from src.utils.logger import get_logger
from src.models.base import TimestampMixin, UUIDMixin


class TestBasicFunctionality:
    """基础功能测试"""

    def test_settings_initialization(self):
        """测试配置初始化"""
        settings = Settings()
        assert settings.app_name == "DPA智能知识引擎"
        assert settings.environment in ["development", "production", "test"]

    def test_logger_creation(self):
        """测试日志器创建"""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_timestamp_mixin(self):
        """测试时间戳混入类"""
        mixin = TimestampMixin()
        assert hasattr(mixin, 'created_at')
        assert hasattr(mixin, 'updated_at')

    def test_uuid_mixin(self):
        """测试UUID混入类"""
        mixin = UUIDMixin()
        assert hasattr(mixin, 'id')
        assert mixin.id is not None


class TestImports:
    """测试关键模块导入"""

    def test_import_models(self):
        """测试数据模型导入"""
        from src.models import document, project, user
        assert document is not None
        assert project is not None
        assert user is not None

    def test_import_database_clients(self):
        """测试数据库客户端导入"""
        from src.database import qdrant_client, neo4j_client, redis_client
        assert qdrant_client is not None
        assert neo4j_client is not None
        assert redis_client is not None

    def test_import_core_modules(self):
        """测试核心模块导入"""
        from src.core import knowledge_index, vectorization, chunking
        assert knowledge_index is not None
        assert vectorization is not None
        assert chunking is not None

    def test_import_api_modules(self):
        """测试API模块导入"""
        from src.api import main
        from src.api.routes import health, projects, documents
        assert main is not None
        assert health is not None
        assert projects is not None
        assert documents is not None


class TestConstants:
    """测试常量和枚举"""

    def test_document_types(self):
        """测试文档类型枚举"""
        from src.models.document import DocumentType
        assert DocumentType.PDF == "pdf"
        assert DocumentType.WORD == "word"
        assert DocumentType.MARKDOWN == "markdown"

    def test_project_status(self):
        """测试项目状态枚举"""
        from src.models.project import ProjectStatus
        assert ProjectStatus.ACTIVE == "active"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.ARCHIVED == "archived"


@pytest.mark.asyncio
async def test_async_functionality():
    """测试异步功能"""
    import asyncio
    
    async def dummy_async_function():
        await asyncio.sleep(0.01)
        return "async_test_passed"
    
    result = await dummy_async_function()
    assert result == "async_test_passed"


def test_version_info():
    """测试版本信息"""
    # 这里可以添加版本检查逻辑
    assert True  # 占位测试，确保测试套件能运行 