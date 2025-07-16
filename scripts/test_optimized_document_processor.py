#!/usr/bin/env python3
"""
测试优化后的文档处理流程
验证文档解析优化、质量评估和批量处理功能
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.graphs.simplified_document_processor import SimplifiedDocumentProcessor, ProcessingMode
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_document_parsing_optimization():
    """测试文档解析优化"""
    print("\n=== 测试文档解析优化 ===")
    
    processor = SimplifiedDocumentProcessor()
    
    # 创建测试文档
    test_files = {
        "test_utf8.txt": "这是一个UTF-8编码的测试文档。\n包含中文内容。\n测试解析器的编码处理能力。",
        "test_academic.txt": """
        Abstract
        This research paper investigates the application of machine learning in natural language processing.
        
        Introduction
        Natural language processing (NLP) has seen significant advances in recent years...
        
        Methods
        We employed a transformer-based architecture to process text data...
        
        Conclusion
        Our findings demonstrate the effectiveness of modern NLP techniques...
        
        References
        [1] Vaswani et al., "Attention is All You Need", 2017
        """,
        "test_code.py": """
        def process_data(data):
            '''Process input data and return results'''
            results = []
            for item in data:
                if validate_item(item):
                    results.append(transform_item(item))
            return results
        
        class DataProcessor:
            def __init__(self, config):
                self.config = config
        """
    }
    
    # 创建临时测试文件
    test_dir = Path("data/test_documents")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, content in test_files.items():
        file_path = test_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # 测试每个文件
    for filename in test_files:
        file_path = test_dir / filename
        print(f"\n测试文件: {filename}")
        
        try:
            state = await processor.process_document({
                "document_id": f"test_{filename}",
                "project_id": "test_project",
                "file_path": str(file_path),
                "file_name": filename,
                "mode": ProcessingMode.STANDARD
            })
            
            # 检查结果
            if state["success"]:
                print(f"✓ 解析成功")
                print(f"  - 内容长度: {len(state['content'])} 字符")
                print(f"  - 分块数量: {len(state['chunks'])}")
                print(f"  - 文档类型: {state['metadata']['quality_assessment']['content_type']}")
                print(f"  - 质量评分: {state['metadata']['quality_assessment']['overall_score']:.2f}")
                print(f"  - 处理时间: {state['processing_time_seconds']:.2f}秒")
            else:
                print(f"✗ 解析失败: {state['error_message']}")
                
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            logger.error(f"Error testing {filename}: {e}")
    
    # 清理测试文件
    for filename in test_files:
        (test_dir / filename).unlink(missing_ok=True)


async def test_document_quality_assessment():
    """测试文档质量评估功能"""
    print("\n\n=== 测试文档质量评估 ===")
    
    processor = SimplifiedDocumentProcessor()
    
    # 创建不同质量的测试文档
    quality_test_cases = {
        "high_quality.txt": """
        Introduction to Machine Learning

        Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience. Unlike traditional programming where explicit instructions are provided, machine learning systems learn patterns from data.

        Types of Machine Learning

        There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning involves training models on labeled data, where the desired output is known. Unsupervised learning works with unlabeled data to discover hidden patterns. Reinforcement learning involves agents learning through interaction with an environment.

        Applications in Industry

        Machine learning has revolutionized various industries. In healthcare, it aids in disease diagnosis and drug discovery. In finance, it powers fraud detection and algorithmic trading. The technology sector uses it for recommendation systems and natural language processing.

        Future Prospects

        As computational power increases and data becomes more abundant, machine learning will continue to evolve. Deep learning, a subset of machine learning, has shown remarkable results in image recognition and natural language understanding. The future holds promise for more sophisticated and efficient learning algorithms.
        """,
        
        "low_quality.txt": "ML is good. It helps. Very useful.",
        
        "medium_quality.txt": """
        Machine learning is important. It has many uses. Companies use it a lot.
        
        There are different types. Some are supervised. Others are not.
        
        It will grow in the future.
        """
    }
    
    test_dir = Path("data/test_documents")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, content in quality_test_cases.items():
        file_path = test_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n测试文档: {filename}")
        
        try:
            state = await processor.process_document({
                "document_id": f"quality_test_{filename}",
                "project_id": "test_project",
                "file_path": str(file_path),
                "file_name": filename,
                "mode": ProcessingMode.STANDARD
            })
            
            if state["success"]:
                qa = state['metadata']['quality_assessment']
                print(f"质量评估结果:")
                print(f"  - 总体评分: {qa['overall_score']:.2f}")
                print(f"  - 内容长度评分: {qa['content_length']:.2f}")
                print(f"  - 分块均匀性: {qa['chunk_uniformity']:.2f}")
                print(f"  - 文本密度: {qa['text_density']:.2f}")
                print(f"  - 可读性: {qa['readability']:.2f}")
                print(f"  - 内容类型: {qa['content_type']}")
                
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
    
    # 清理
    for filename in quality_test_cases:
        (test_dir / filename).unlink(missing_ok=True)


async def test_batch_processing():
    """测试批量处理优化"""
    print("\n\n=== 测试批量处理优化 ===")
    
    processor = SimplifiedDocumentProcessor()
    
    # 创建多个测试文档
    test_dir = Path("data/test_documents")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    documents = []
    for i in range(5):
        filename = f"batch_test_{i}.txt"
        file_path = test_dir / filename
        content = f"This is test document {i}. " * 50  # 创建一些内容
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        documents.append({
            "document_id": f"batch_{i}",
            "project_id": "test_project",
            "file_path": str(file_path),
            "file_name": filename,
            "mode": ProcessingMode.FAST
        })
    
    print(f"批量处理 {len(documents)} 个文档...")
    
    # 测试批量处理
    start_time = datetime.now()
    results = await processor.process_batch(documents, max_concurrent=3)
    end_time = datetime.now()
    
    total_time = (end_time - start_time).total_seconds()
    
    # 分析结果
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    
    print(f"\n批量处理结果:")
    print(f"  - 成功: {successful}/{len(documents)}")
    print(f"  - 失败: {failed}")
    print(f"  - 总处理时间: {total_time:.2f}秒")
    print(f"  - 平均每文档: {total_time/len(documents):.2f}秒")
    
    # 显示每个文档的结果
    for i, result in enumerate(results):
        if result.get("success"):
            print(f"  - 文档{i}: ✓ ({result['processing_time_seconds']:.2f}秒)")
        else:
            print(f"  - 文档{i}: ✗ ({result.get('error_message', 'Unknown error')})")
    
    # 清理
    for doc in documents:
        Path(doc['file_path']).unlink(missing_ok=True)


async def test_mode_comparison():
    """比较STANDARD和FAST模式"""
    print("\n\n=== 比较处理模式 ===")
    
    processor = SimplifiedDocumentProcessor()
    
    # 创建测试文档
    test_content = """
    Natural Language Processing with Deep Learning
    
    Deep learning has revolutionized the field of natural language processing (NLP) in recent years. 
    Traditional NLP methods relied heavily on hand-crafted features and rule-based systems. However, 
    the advent of deep neural networks has enabled models to automatically learn representations from data.
    
    """ * 20  # 重复内容以创建较大文档
    
    test_dir = Path("data/test_documents")
    test_dir.mkdir(parents=True, exist_ok=True)
    file_path = test_dir / "mode_test.txt"
    
    with open(file_path, 'w') as f:
        f.write(test_content)
    
    modes = [ProcessingMode.STANDARD, ProcessingMode.FAST]
    results = {}
    
    for mode in modes:
        print(f"\n测试 {mode.value} 模式...")
        
        state = await processor.process_document({
            "document_id": f"mode_test_{mode.value}",
            "project_id": "test_project",
            "file_path": str(file_path),
            "file_name": "mode_test.txt",
            "mode": mode
        })
        
        if state["success"]:
            results[mode.value] = {
                "chunks": len(state["chunks"]),
                "avg_chunk_size": sum(len(c["content"]) for c in state["chunks"]) / len(state["chunks"]),
                "time": state["processing_time_seconds"],
                "quality_score": state["metadata"]["quality_assessment"]["overall_score"]
            }
            
            print(f"  - 分块数: {results[mode.value]['chunks']}")
            print(f"  - 平均块大小: {results[mode.value]['avg_chunk_size']:.0f}")
            print(f"  - 处理时间: {results[mode.value]['time']:.2f}秒")
            print(f"  - 质量评分: {results[mode.value]['quality_score']:.2f}")
    
    # 比较结果
    if len(results) == 2:
        print(f"\n性能对比:")
        print(f"  - FAST模式速度提升: {(results['standard']['time'] / results['fast']['time'] - 1) * 100:.1f}%")
        print(f"  - FAST模式块数减少: {(1 - results['fast']['chunks'] / results['standard']['chunks']) * 100:.1f}%")
    
    # 清理
    file_path.unlink(missing_ok=True)


async def main():
    """运行所有测试"""
    print("=== 文档处理优化测试 ===")
    print(f"开始时间: {datetime.now()}")
    
    try:
        # 运行各项测试
        await test_document_parsing_optimization()
        await test_document_quality_assessment()
        await test_batch_processing()
        await test_mode_comparison()
        
        print(f"\n\n✅ 所有测试完成!")
        print(f"结束时间: {datetime.now()}")
        
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现错误: {str(e)}")
        logger.error(f"Test error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())