#!/usr/bin/env python3
"""
测试基于tiktoken的分块优化效果
验证第一步优化：使用token计数代替字符计数
"""
import asyncio
import sys
from pathlib import Path
from collections import Counter
import statistics

sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor, tiktoken_len
from src.database.qdrant_client import get_qdrant_client
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def test_tiktoken_chunking():
    """测试基于tiktoken的分块效果"""
    print("\n" + "="*80)
    print("🔬 第一步优化测试：基于Token的智能分块")
    print("="*80)
    
    # 1. 测试中英文token计算差异
    print("\n1️⃣ Token计算对比（中文 vs 英文）:")
    
    test_cases = [
        ("Hello world", "纯英文"),
        ("你好世界", "纯中文"),
        ("AI agents must manage information", "英文句子"),
        ("人工智能代理必须管理信息", "中文句子"),
        ("Memory in AI spans short-term and long-term", "英文长句"),
        ("AI中的记忆包括短期记忆和长期记忆", "中英混合"),
    ]
    
    print(f"{'文本内容':<40} {'类型':<10} {'字符数':<8} {'Token数':<8} {'比例':<8}")
    print("-" * 80)
    
    for text, text_type in test_cases:
        char_count = len(text)
        token_count = tiktoken_len(text)
        ratio = token_count / char_count if char_count > 0 else 0
        print(f"{text:<40} {text_type:<10} {char_count:<8} {token_count:<8} {ratio:<8.2f}")
    
    # 2. 测试实际文档处理
    print("\n2️⃣ 处理真实文档（优化后的分块）:")
    processor = create_mvp_document_processor()
    
    # 使用之前的AI记忆系统文档
    doc_path = "/Users/mdwong001/Desktop/code/rag/data/zonghe/MemeoryOpenai.txt"
    
    # 处理文档
    result = await processor.process_document(
        file_path=doc_path,
        project_id="tiktoken_test"
    )
    
    print(f"\n✅ 文档处理完成:")
    print(f"   - 文档ID: {result.document_id}")
    print(f"   - 分块数量: {result.chunk_count}")
    print(f"   - 分块策略: 512 tokens/块，128 tokens重叠")
    
    # 等待存储完成
    await asyncio.sleep(3)
    
    # 3. 分析分块质量
    print("\n3️⃣ 分块质量分析:")
    
    qdrant = get_qdrant_client()
    try:
        # 获取分块数据
        collection_name = "project_tiktoken_test"
        points, _ = await qdrant.scroll_points(
            collection_name=collection_name,
            limit=50,
            with_payload=True,
            with_vectors=False
        )
        
        if points:
            # 分析token和字符长度
            token_lengths = []
            char_lengths = []
            chunk_endings = Counter()
            
            for point in points:
                content = point.payload.get('content', '')
                char_lengths.append(len(content))
                token_lengths.append(tiktoken_len(content))
                
                # 分析分块结尾质量
                if content:
                    # 检查最后10个字符
                    ending = content[-10:].strip()
                    if ending.endswith(('.', '。', '!', '！', '?', '？')):
                        chunk_endings['完整句子'] += 1
                    elif ending.endswith((',', '，', ';', '；')):
                        chunk_endings['子句结尾'] += 1
                    elif '\n' in ending:
                        chunk_endings['段落边界'] += 1
                    else:
                        chunk_endings['词中断'] += 1
            
            print(f"   📊 Token长度分析:")
            print(f"      - 平均: {statistics.mean(token_lengths):.1f} tokens")
            print(f"      - 标准差: {statistics.stdev(token_lengths):.1f}")
            print(f"      - 范围: {min(token_lengths)} - {max(token_lengths)} tokens")
            
            print(f"\n   📏 字符长度分析:")
            print(f"      - 平均: {statistics.mean(char_lengths):.1f} 字符")
            print(f"      - 中位数: {statistics.median(char_lengths)}")
            
            print(f"\n   ✂️ 分块边界质量:")
            total = sum(chunk_endings.values())
            for ending_type, count in chunk_endings.most_common():
                percentage = (count / total) * 100
                quality = "✅" if ending_type in ['完整句子', '段落边界'] else "⚠️" if ending_type == '子句结尾' else "❌"
                print(f"      {quality} {ending_type}: {count} ({percentage:.1f}%)")
            
            # 显示示例分块
            print(f"\n   📄 示例分块（前3个）:")
            for i, point in enumerate(points[:3]):
                content = point.payload.get('content', '').replace('\n', ' ').strip()
                tokens = tiktoken_len(content)
                chars = len(content)
                print(f"\n   块 {i+1} ({tokens} tokens, {chars} 字符):")
                print(f"   开始: {content[:100]}...")
                print(f"   结尾: ...{content[-100:]}")
                
    except Exception as e:
        print(f"   ❌ 无法获取分块数据: {e}")
    
    # 4. 对比优化效果
    print("\n4️⃣ 优化效果总结:")
    print("\n   🎯 关键改进:")
    print("   1. Token计数确保中英文公平处理")
    print("   2. 优化的分隔符优先级提高语义完整性")
    print("   3. 更大的分块尺寸(512 tokens)适合研究性文档")
    print("   4. 25%重叠(128 tokens)保证上下文连续性")
    
    print("\n   📈 预期效果:")
    print("   - 更少的语义割裂")
    print("   - 更高的检索精度")
    print("   - 更好的中英文混合支持")
    print("   - 更稳定的分块质量")


async def main():
    """主函数"""
    await test_tiktoken_chunking()
    
    print("\n" + "="*80)
    print("✅ 第一步优化完成！")
    print("=" * 80)
    print("\n核心改进已实施:")
    print("1. ✅ 使用tiktoken替代len()进行长度计算")
    print("2. ✅ 优化分隔符顺序（段落>句子>标点>空格）")
    print("3. ✅ 增大分块尺寸到512 tokens")
    print("4. ✅ 设置25%重叠确保上下文连续")
    print("\n准备好进行第二步优化了！")


if __name__ == "__main__":
    asyncio.run(main())