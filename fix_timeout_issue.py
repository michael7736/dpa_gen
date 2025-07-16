#!/usr/bin/env python3
"""
修复超时问题的脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/Users/mdwong001/Desktop/code/rag/DPA')

# 设置环境变量
os.environ['PYTHONPATH'] = '/Users/mdwong001/Desktop/code/rag/DPA'

async def analyze_timeout_issue():
    """分析超时问题"""
    print("🔍 分析处理管道超时问题")
    print("=" * 60)
    
    # 1. 检查管道执行器实现
    print("\n1️⃣ 检查管道执行器...")
    try:
        from src.services.pipeline_executor import PipelineExecutor, get_pipeline_executor
        executor = get_pipeline_executor()
        print(f"   ✅ 管道执行器实例: {type(executor)}")
        
        # 检查阶段执行器
        print(f"   📋 支持的阶段:")
        for stage, func in executor.stage_executors.items():
            print(f"   - {stage}: {func.__name__}")
            
    except Exception as e:
        print(f"   ❌ 管道执行器导入失败: {e}")
        return
    
    # 2. 检查后台任务机制
    print("\n2️⃣ 检查后台任务...")
    try:
        from src.api.routes.documents_v2 import execute_pipeline_background
        print(f"   ✅ 后台任务函数: {execute_pipeline_background.__name__}")
        
        # 检查BackgroundTasks
        from fastapi import BackgroundTasks
        bg_tasks = BackgroundTasks()
        print(f"   ✅ BackgroundTasks: {type(bg_tasks)}")
        
    except Exception as e:
        print(f"   ❌ 后台任务检查失败: {e}")
    
    # 3. 检查数据库连接
    print("\n3️⃣ 检查数据库连接...")
    try:
        from src.database.postgresql import get_session
        from src.models.processing_pipeline import ProcessingPipeline
        
        print(f"   ✅ 数据库会话: {get_session}")
        print(f"   ✅ 管道模型: {ProcessingPipeline}")
        
    except Exception as e:
        print(f"   ❌ 数据库连接检查失败: {e}")
    
    # 4. 检查WebSocket通知
    print("\n4️⃣ 检查WebSocket通知...")
    try:
        from src.api.websocket import get_progress_notifier
        notifier = get_progress_notifier()
        print(f"   ✅ WebSocket通知器: {type(notifier)}")
        
    except Exception as e:
        print(f"   ❌ WebSocket通知检查失败: {e}")
    
    # 5. 分析可能的问题
    print("\n5️⃣ 分析潜在问题...")
    
    issues = []
    
    # 检查execute_pipeline_background函数
    print("   检查后台任务实现...")
    try:
        import inspect
        from src.api.routes.documents_v2 import execute_pipeline_background
        
        # 获取函数源码
        source = inspect.getsource(execute_pipeline_background)
        
        # 检查是否有异常处理
        if "try:" in source and "except:" in source:
            print("   ✅ 后台任务有异常处理")
        else:
            issues.append("后台任务缺乏异常处理")
        
        # 检查是否有日志记录
        if "logger" in source:
            print("   ✅ 后台任务有日志记录")
        else:
            issues.append("后台任务缺少日志记录")
            
    except Exception as e:
        print(f"   ❌ 无法分析后台任务: {e}")
        issues.append("无法分析后台任务源码")
    
    # 6. 生成修复建议
    print("\n6️⃣ 修复建议:")
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("   ✅ 未发现明显问题")
    
    # 7. 创建修复方案
    print("\n7️⃣ 创建修复方案...")
    
    # 检查execute_pipeline_background函数
    try:
        from src.api.routes.documents_v2 import execute_pipeline_background
        
        # 创建改进版本
        improved_function = '''
async def execute_pipeline_background_improved(pipeline_id: str, db_session):
    """改进的后台管道执行函数"""
    import asyncio
    from src.services.pipeline_executor import get_pipeline_executor
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    try:
        logger.info(f"开始执行管道: {pipeline_id}")
        
        # 获取执行器
        executor = get_pipeline_executor()
        
        # 设置超时
        timeout = 300  # 5分钟超时
        
        # 执行管道
        await asyncio.wait_for(
            executor.execute(pipeline_id, db_session),
            timeout=timeout
        )
        
        logger.info(f"管道执行完成: {pipeline_id}")
        
    except asyncio.TimeoutError:
        logger.error(f"管道执行超时: {pipeline_id}")
        # 标记管道为失败
        try:
            from src.models.processing_pipeline import ProcessingPipeline
            pipeline = db_session.query(ProcessingPipeline).filter(
                ProcessingPipeline.id == pipeline_id
            ).first()
            if pipeline:
                pipeline.interrupted = True
                db_session.commit()
        except Exception as e:
            logger.error(f"标记管道失败时出错: {e}")
            
    except Exception as e:
        logger.error(f"管道执行异常: {pipeline_id} - {e}")
        import traceback
        logger.error(traceback.format_exc())
'''
        
        # 保存改进版本
        with open('/Users/mdwong001/Desktop/code/rag/DPA/improved_pipeline_function.py', 'w') as f:
            f.write(improved_function)
        
        print("   ✅ 创建改进版本: improved_pipeline_function.py")
        
    except Exception as e:
        print(f"   ❌ 创建改进版本失败: {e}")
    
    print("\n✅ 分析完成")

if __name__ == "__main__":
    asyncio.run(analyze_timeout_issue())