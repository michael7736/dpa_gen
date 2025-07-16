#!/usr/bin/env python3
"""
向量索引优化工具
优化Qdrant集合的索引配置以提高检索性能
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, OptimizersConfig, 
    HnswConfigDiff, QuantizationConfig, ScalarQuantization,
    CollectionConfig, PayloadSchemaType
)

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorIndexOptimizer:
    """向量索引优化器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port
        )
    
    async def analyze_collection(self, collection_name: str):
        """分析集合状态"""
        try:
            # 获取集合信息
            info = self.client.get_collection(collection_name)
            
            logger.info(f"\n=== 集合分析: {collection_name} ===")
            logger.info(f"向量数量: {info.points_count}")
            logger.info(f"索引状态: {info.status}")
            logger.info(f"配置: {info.config}")
            
            # 获取索引统计
            if hasattr(info, 'optimizer_status'):
                logger.info(f"优化器状态: {info.optimizer_status}")
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to analyze collection: {e}")
            return None
    
    async def optimize_hnsw_index(self, collection_name: str):
        """优化HNSW索引参数"""
        logger.info(f"\n优化HNSW索引: {collection_name}")
        
        try:
            # 获取当前集合信息
            info = self.client.get_collection(collection_name)
            points_count = info.points_count
            
            # 根据数据量选择优化参数
            if points_count < 10000:
                # 小数据集
                hnsw_config = HnswConfigDiff(
                    m=16,  # 每个节点的连接数
                    ef_construct=100,  # 构建时的搜索深度
                    full_scan_threshold=1000  # 全扫描阈值
                )
            elif points_count < 100000:
                # 中等数据集
                hnsw_config = HnswConfigDiff(
                    m=32,
                    ef_construct=200,
                    full_scan_threshold=5000
                )
            else:
                # 大数据集
                hnsw_config = HnswConfigDiff(
                    m=64,
                    ef_construct=400,
                    full_scan_threshold=10000
                )
            
            # 更新集合配置
            self.client.update_collection(
                collection_name=collection_name,
                hnsw_config=hnsw_config
            )
            
            logger.info(f"HNSW索引已优化: m={hnsw_config.m}, ef_construct={hnsw_config.ef_construct}")
            
        except Exception as e:
            logger.error(f"Failed to optimize HNSW index: {e}")
    
    async def enable_quantization(self, collection_name: str):
        """启用量化以减少内存使用"""
        logger.info(f"\n启用量化: {collection_name}")
        
        try:
            # 标量量化配置
            quantization_config = ScalarQuantization(
                type="int8",  # 8位整数量化
                quantile=0.99,  # 分位数
                always_ram=True  # 始终在内存中
            )
            
            # 更新集合配置
            self.client.update_collection(
                collection_name=collection_name,
                quantization_config=quantization_config
            )
            
            logger.info("量化已启用，内存使用将减少约75%")
            
        except Exception as e:
            logger.error(f"Failed to enable quantization: {e}")
    
    async def optimize_payload_indexing(self, collection_name: str):
        """优化payload索引"""
        logger.info(f"\n优化payload索引: {collection_name}")
        
        try:
            # 创建常用字段的索引
            common_fields = [
                ("document_id", PayloadSchemaType.KEYWORD),
                ("project_id", PayloadSchemaType.KEYWORD),
                ("created_at", PayloadSchemaType.DATETIME),
                ("file_name", PayloadSchemaType.TEXT),
                ("chunk_index", PayloadSchemaType.INTEGER)
            ]
            
            for field_name, field_type in common_fields:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_type
                    )
                    logger.info(f"创建索引: {field_name} ({field_type})")
                except Exception as e:
                    logger.warning(f"索引可能已存在: {field_name} - {e}")
            
        except Exception as e:
            logger.error(f"Failed to optimize payload indexing: {e}")
    
    async def optimize_search_params(self, collection_name: str):
        """优化搜索参数"""
        logger.info(f"\n优化搜索参数建议:")
        
        try:
            info = self.client.get_collection(collection_name)
            points_count = info.points_count
            
            # 根据数据量给出建议
            if points_count < 10000:
                logger.info("- 搜索时使用 ef=64 (小数据集)")
                logger.info("- 可以使用 exact=True 获得精确结果")
            elif points_count < 100000:
                logger.info("- 搜索时使用 ef=128 (中等数据集)")
                logger.info("- 使用 quantization.rescore=True 提高精度")
            else:
                logger.info("- 搜索时使用 ef=256 (大数据集)")
                logger.info("- 考虑使用分片和并行搜索")
                logger.info("- 使用 quantization.oversampling=2.0")
            
            # 通用建议
            logger.info("\n通用优化建议:")
            logger.info("- 批量搜索时使用 search_batch 方法")
            logger.info("- 预热查询：在生产环境启动时执行一些典型查询")
            logger.info("- 监控查询延迟并调整 ef 参数")
            
        except Exception as e:
            logger.error(f"Failed to generate search recommendations: {e}")
    
    async def create_optimized_collection(
        self, 
        collection_name: str,
        vector_size: int = 3072
    ):
        """创建优化的集合"""
        logger.info(f"\n创建优化集合: {collection_name}")
        
        try:
            # 优化的配置
            vectors_config = VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
            
            # HNSW配置
            hnsw_config = HnswConfigDiff(
                m=32,
                ef_construct=200,
                full_scan_threshold=5000,
                max_indexing_threads=0  # 使用所有CPU核心
            )
            
            # 优化器配置
            optimizers_config = OptimizersConfig(
                default_segment_number=4,  # 默认分片数
                memmap_threshold=50000,  # 内存映射阈值
                indexing_threshold=20000,  # 索引阈值
                flush_interval_sec=10  # 刷新间隔
            )
            
            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                hnsw_config=hnsw_config,
                optimizers_config=optimizers_config
            )
            
            logger.info(f"优化集合创建成功: {collection_name}")
            
            # 创建基础索引
            await self.optimize_payload_indexing(collection_name)
            
        except Exception as e:
            logger.error(f"Failed to create optimized collection: {e}")
    
    async def benchmark_collection(self, collection_name: str):
        """基准测试集合性能"""
        logger.info(f"\n基准测试: {collection_name}")
        
        try:
            import time
            import numpy as np
            
            # 生成测试向量
            test_vector = np.random.rand(3072).tolist()
            
            # 测试不同的搜索参数
            test_configs = [
                {"limit": 10, "ef": 64},
                {"limit": 10, "ef": 128},
                {"limit": 10, "ef": 256},
                {"limit": 50, "ef": 128},
                {"limit": 100, "ef": 128}
            ]
            
            for config in test_configs:
                times = []
                for _ in range(5):  # 5次测试取平均
                    start = time.time()
                    results = self.client.search(
                        collection_name=collection_name,
                        query_vector=test_vector,
                        limit=config["limit"],
                        search_params={"hnsw_ef": config["ef"]}
                    )
                    times.append(time.time() - start)
                
                avg_time = sum(times) / len(times)
                logger.info(f"配置 {config}: 平均耗时 {avg_time*1000:.2f}ms")
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")


async def main():
    """主函数"""
    optimizer = VectorIndexOptimizer()
    
    # 列出所有集合
    try:
        collections = optimizer.client.get_collections().collections
        logger.info(f"\n发现 {len(collections)} 个集合:")
        for col in collections:
            logger.info(f"- {col.name}")
        
        # 如果有集合，优化第一个
        if collections:
            collection_name = collections[0].name
            
            # 分析集合
            await optimizer.analyze_collection(collection_name)
            
            # 优化索引
            await optimizer.optimize_hnsw_index(collection_name)
            
            # 优化payload索引
            await optimizer.optimize_payload_indexing(collection_name)
            
            # 提供搜索参数建议
            await optimizer.optimize_search_params(collection_name)
            
            # 运行基准测试
            await optimizer.benchmark_collection(collection_name)
        else:
            # 创建优化的测试集合
            await optimizer.create_optimized_collection("optimized_test_collection")
        
        logger.info("\n✅ 向量索引优化完成！")
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())