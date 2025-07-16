#!/usr/bin/env python3
"""
测试高级文档分析API集成
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.graphs.advanced_document_analyzer import AdvancedDocumentAnalyzer, AnalysisDepth
from src.config.settings import get_settings

async def test_analyzer_directly():
    """直接测试分析器（不通过API）"""
    print("=== 直接测试高级文档分析器 ===\n")
    
    # 创建分析器实例
    analyzer = AdvancedDocumentAnalyzer()
    
    # 测试文本
    test_content = """
    人工智能（AI）正在彻底改变教育领域。通过个性化学习系统，AI能够根据每个学生的学习速度和风格定制教育内容。
    
    主要优势：
    1. 个性化学习路径：AI可以分析学生的学习模式，提供定制化的学习材料
    2. 即时反馈：学生可以立即获得作业和测试的反馈
    3. 24/7可用性：AI助手随时可以回答学生的问题
    
    研究表明，使用AI辅助学习的学生平均成绩提高了30%。MIT的一项研究发现，使用AI辅导系统的学生在数学成绩上平均提高了23%。
    
    然而，这也带来了新的挑战：
    - 数据隐私：学生的学习数据如何保护？
    - 教师角色转变：从知识传授者到学习引导者
    - 数字鸿沟：并非所有学生都有平等的技术访问机会
    
    未来展望：
    混合式学习模式将成为主流，结合AI的效率和人类教师的创造力与同理心。预计到2030年，全球70%的教育机构将采用某种形式的AI辅助教学。
    """
    
    # 准备文档信息
    document_info = {
        "document_id": "test_doc_001",
        "project_id": "test_project",
        "user_id": "test_user",
        "file_path": "memory",
        "file_name": "AI教育应用研究.txt",
        "content": test_content,
        "analysis_depth": AnalysisDepth.STANDARD,
        "analysis_goal": "深入理解AI在教育中的应用、优势、挑战和未来发展"
    }
    
    try:
        print("开始分析...")
        print(f"分析深度: {document_info['analysis_depth']}")
        print(f"分析目标: {document_info['analysis_goal']}")
        print("-" * 50)
        
        # 执行分析
        result = await analyzer.analyze_document(document_info)
        
        if result["success"]:
            print("\n✅ 分析成功！")
            print(f"处理时间: {result.get('processing_time', 0):.2f}秒")
            
            results = result["results"]
            
            # 打印执行摘要
            print("\n📋 执行摘要:")
            print("-" * 50)
            print(results.get("executive_summary", "无"))
            
            # 打印关键洞察
            print("\n💡 关键洞察:")
            print("-" * 50)
            for i, insight in enumerate(results.get("key_insights", [])[:5], 1):
                print(f"{i}. {insight}")
            
            # 打印建议
            print("\n📌 建议:")
            print("-" * 50)
            for i, rec in enumerate(results.get("recommendations", [])[:5], 1):
                print(f"{i}. {rec}")
            
            # 打印质量评分
            print(f"\n⭐ 文档质量评分: {results.get('quality_score', 0):.2f}/1.0")
            
            # 如果有详细报告，显示部分内容
            if results.get("detailed_report"):
                print("\n📊 详细报告概览:")
                print("-" * 50)
                report = results["detailed_report"]
                if "document_overview" in report:
                    overview = report["document_overview"]
                    print(f"文档类型: {overview.get('type', '未知')}")
                    print(f"主要主题: {', '.join(overview.get('main_topics', [])[:3])}")
                
        else:
            print(f"\n❌ 分析失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_different_depths():
    """测试不同的分析深度"""
    print("\n\n=== 测试不同分析深度 ===\n")
    
    analyzer = AdvancedDocumentAnalyzer()
    
    test_content = "AI正在改变教育。个性化学习和即时反馈是主要优势。"
    
    depths = [
        (AnalysisDepth.BASIC, "基础分析"),
        (AnalysisDepth.STANDARD, "标准分析"),
    ]
    
    for depth, name in depths:
        print(f"\n--- {name} ({depth}) ---")
        
        document_info = {
            "document_id": f"test_depth_{depth}",
            "project_id": "test_project",
            "user_id": "test_user",
            "file_path": "memory",
            "file_name": "test.txt",
            "content": test_content,
            "analysis_depth": depth
        }
        
        try:
            result = await analyzer.analyze_document(document_info)
            if result["success"]:
                print(f"✅ 成功 - 处理时间: {result.get('processing_time', 0):.2f}秒")
                summary = result["results"].get("executive_summary", "")
                if summary:
                    print(f"摘要: {summary[:100]}...")
            else:
                print(f"❌ 失败: {result.get('error')}")
        except Exception as e:
            print(f"❌ 错误: {str(e)}")


def main():
    """主函数"""
    print("🚀 开始测试高级文档分析器集成")
    print("=" * 60)
    
    # 运行异步测试
    asyncio.run(test_analyzer_directly())
    
    # 测试不同深度
    # asyncio.run(test_different_depths())
    
    print("\n\n✅ 测试完成！")
    print("\n💡 提示：")
    print("1. 要通过API测试，请先启动服务: ./start_api.sh")
    print("2. 然后运行: python test_analysis_quick.py")
    print("3. 查看API文档: http://localhost:8001/docs")


if __name__ == "__main__":
    main()