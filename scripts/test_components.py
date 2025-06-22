#!/usr/bin/env python3
"""
DPA系统组件测试脚本
测试各个核心组件的连接状态和基本功能
"""

import asyncio
import os
import sys
from typing import Dict, Any
import traceback
from datetime import datetime

# 添加src路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from config.settings import get_settings
except ImportError:
    print("❌ 配置模块导入失败，请确保已正确设置环境变量")
    sys.exit(1)

class ComponentTester:
    """组件测试器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.results = {}
        
    def log_result(self, component: str, status: str, message: str, details: Any = None):
        """记录测试结果"""
        self.results[component] = {
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # 实时输出结果
        status_icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        print(f"{status_icon} {component}: {message}")
        if details and status == "error":
            print(f"   详细信息: {details}")
    
    async def test_postgresql(self):
        """测试PostgreSQL连接"""
        try:
            import psycopg2
            from psycopg2 import sql
            
            # 使用配置中的数据库URL
            conn_str = self.settings.database.url
            
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            
            # 测试基本查询
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.log_result("PostgreSQL", "success", f"连接成功", {"version": version})
            
        except Exception as e:
            self.log_result("PostgreSQL", "error", f"连接失败", str(e))
    
    async def test_redis(self):
        """测试Redis连接"""
        try:
            import redis
            
            # 使用配置中的Redis URL
            client = redis.from_url(
                self.settings.redis.url,
                decode_responses=True
            )
            
            # 测试基本操作
            client.set("test_key", "test_value", ex=10)
            value = client.get("test_key")
            client.delete("test_key")
            
            info = client.info()
            
            self.log_result("Redis", "success", f"连接成功", {
                "version": info.get("redis_version"),
                "test_operation": "写入/读取/删除成功"
            })
            
        except Exception as e:
            self.log_result("Redis", "error", f"连接失败", str(e))
    
    async def test_qdrant(self):
        """测试Qdrant连接"""
        try:
            from qdrant_client import QdrantClient
            
            # 使用配置中的Qdrant URL
            client = QdrantClient(url=self.settings.qdrant.url)
            
            # 测试连接
            info = client.get_cluster_info()
            collections = client.get_collections()
            
            self.log_result("Qdrant", "success", f"连接成功", {
                "status": info.status,
                "collections_count": len(collections.collections)
            })
            
        except Exception as e:
            self.log_result("Qdrant", "error", f"连接失败", str(e))
    
    async def test_neo4j(self):
        """测试Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.settings.neo4j.url,
                auth=(self.settings.neo4j.username, self.settings.neo4j.password)
            )
            
            # 测试连接
            with driver.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                components = [record for record in result]
                
            driver.close()
            
            self.log_result("Neo4j", "success", f"连接成功", {
                "components": len(components),
                "edition": components[0]["edition"] if components else "unknown"
            })
            
        except Exception as e:
            self.log_result("Neo4j", "error", f"连接失败", str(e))
    
    async def test_openrouter_api(self):
        """测试OpenRouter API连接"""
        try:
            import openai
            
            client = openai.OpenAI(
                base_url=self.settings.ai_model.openrouter_base_url,
                api_key=self.settings.ai_model.openrouter_api_key
            )
            
            # 测试模型列表获取
            models = client.models.list()
            model_count = len(models.data)
            
            # 测试简单的聊天完成
            response = client.chat.completions.create(
                model=self.settings.ai_model.default_llm_model,
                messages=[{"role": "user", "content": "Hello, this is a test message."}],
                max_tokens=10
            )
            
            self.log_result("OpenRouter API", "success", f"API调用成功", {
                "available_models": model_count,
                "default_model": self.settings.ai_model.default_llm_model,
                "test_response": response.choices[0].message.content[:50] + "..." if response.choices else "No response"
            })
            
        except Exception as e:
            self.log_result("OpenRouter API", "error", f"API调用失败", str(e))
    
    async def test_embedding_model(self):
        """测试嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 加载模型
            model = SentenceTransformer(self.settings.ai_model.default_embedding_model)
            
            # 测试嵌入生成
            test_texts = ["这是一个测试文本", "This is a test text"]
            embeddings = model.encode(test_texts)
            
            self.log_result("Embedding Model", "success", f"模型加载和推理成功", {
                "model_name": self.settings.ai_model.default_embedding_model,
                "embedding_dimension": embeddings.shape[1],
                "test_texts_count": len(test_texts)
            })
            
        except Exception as e:
            self.log_result("Embedding Model", "error", f"模型测试失败", str(e))
    
    async def test_file_storage(self):
        """测试文件存储"""
        try:
            import os
            
            # 检查存储目录
            storage_path = self.settings.file_storage.upload_dir
            os.makedirs(storage_path, exist_ok=True)
            
            # 测试文件写入和读取
            test_file = os.path.join(storage_path, "test_file.txt")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("这是一个测试文件")
            
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            os.remove(test_file)
            
            self.log_result("File Storage", "success", f"文件存储测试成功", {
                "storage_path": storage_path,
                "test_operation": "写入/读取/删除成功"
            })
            
        except Exception as e:
            self.log_result("File Storage", "error", f"文件存储测试失败", str(e))
    
    async def test_core_imports(self):
        """测试核心模块导入"""
        try:
            # 测试核心模块导入
            modules_to_test = [
                "fastapi",
                "langchain",
                "langchain_community",
                "langgraph",
                "qdrant_client",
                "sentence_transformers",
                "neo4j",
                "redis",
                "psycopg2",
                "celery",
                "pydantic"
            ]
            
            imported_modules = []
            failed_modules = []
            
            for module_name in modules_to_test:
                try:
                    __import__(module_name)
                    imported_modules.append(module_name)
                except ImportError as e:
                    failed_modules.append((module_name, str(e)))
            
            if not failed_modules:
                self.log_result("Core Imports", "success", f"所有核心模块导入成功", {
                    "imported_count": len(imported_modules),
                    "modules": imported_modules
                })
            else:
                self.log_result("Core Imports", "warning", f"部分模块导入失败", {
                    "imported": imported_modules,
                    "failed": failed_modules
                })
                
        except Exception as e:
            self.log_result("Core Imports", "error", f"模块导入测试失败", str(e))
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始DPA系统组件测试...")
        print("=" * 60)
        
        # 运行所有测试
        test_functions = [
            self.test_core_imports,
            self.test_postgresql,
            self.test_redis,
            self.test_qdrant,
            self.test_neo4j,
            self.test_openrouter_api,
            self.test_embedding_model,
            self.test_file_storage
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                component_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
                self.log_result(component_name, "error", f"测试执行失败", str(e))
        
        # 输出测试总结
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        
        success_count = sum(1 for r in self.results.values() if r['status'] == 'success')
        warning_count = sum(1 for r in self.results.values() if r['status'] == 'warning')
        error_count = sum(1 for r in self.results.values() if r['status'] == 'error')
        
        print(f"✅ 成功: {success_count}")
        print(f"⚠️  警告: {warning_count}")
        print(f"❌ 失败: {error_count}")
        print(f"📈 总体成功率: {success_count/(success_count+warning_count+error_count)*100:.1f}%")
        
        # 输出失败的组件详情
        if error_count > 0:
            print(f"\n❌ 失败的组件:")
            for component, result in self.results.items():
                if result['status'] == 'error':
                    print(f"   • {component}: {result['message']}")
        
        return self.results

async def main():
    """主函数"""
    tester = ComponentTester()
    results = await tester.run_all_tests()
    
    # 返回适当的退出码
    error_count = sum(1 for r in results.values() if r['status'] == 'error')
    sys.exit(1 if error_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main()) 