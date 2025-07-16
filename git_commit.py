#!/usr/bin/env python3
"""
Git 提交脚本
"""

import subprocess
import sys
from pathlib import Path

def run_git_command(command):
    """运行Git命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git命令失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None

def main():
    """主函数"""
    print("🔧 DPA系统Git提交脚本")
    print("=" * 40)
    
    # 切换到项目目录
    os.chdir("/Users/mdwong001/Desktop/code/rag/DPA")
    
    # 检查Git状态
    print("📋 检查Git状态...")
    status = run_git_command("git status --porcelain")
    if status:
        print("修改的文件:")
        print(status)
    else:
        print("没有需要提交的更改")
        return
    
    # 查看最近的提交
    print("\n📜 最近的提交:")
    recent_commits = run_git_command("git log --oneline -5")
    if recent_commits:
        print(recent_commits)
    
    # 添加所有更改
    print("\n➕ 添加所有更改...")
    run_git_command("git add .")
    
    # 创建提交消息
    commit_message = """fix: 修复DPA系统核心功能问题并添加自动化测试

主要修复:
- 修复API导入错误 (processing_stage模块)
- 修复Redis认证问题 (添加密码配置)
- 修复VectorStore embed_texts错误 (改用EmbeddingService)
- 修复EmbeddingService初始化错误 (添加VectorConfig)
- 修复知识图谱生成问题 (改进实体提取逻辑)
- 修复用户ID UUID格式错误 (添加映射机制)
- 修复Neo4j数据库错误 (使用默认数据库)

新增功能:
- 添加自动化测试脚本 (simple_auto_test.py)
- 添加完整集成测试框架 (auto_test_system.py)
- 添加浏览器端测试工具
- 更新CLAUDE.md文档记录所有修复

技术改进:
- 增强知识图谱实体和关系提取
- 优化错误处理和用户体验
- 完善WebSocket错误处理
- 添加故障处理原则和最佳实践

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""
    
    # 创建提交
    print("\n💾 创建提交...")
    commit_result = run_git_command(f'git commit -m "{commit_message}"')
    if commit_result is not None:
        print("✅ 提交成功!")
        print(commit_result)
    else:
        print("❌ 提交失败")
        return
    
    # 检查是否有远程仓库
    print("\n🔍 检查远程仓库...")
    remote = run_git_command("git remote -v")
    if remote:
        print("远程仓库:")
        print(remote)
        
        # 询问是否推送
        response = input("\n是否推送到远程仓库? (y/n): ")
        if response.lower() == 'y':
            print("\n🚀 推送到远程仓库...")
            push_result = run_git_command("git push")
            if push_result is not None:
                print("✅ 推送成功!")
                print(push_result)
            else:
                print("❌ 推送失败")
        else:
            print("⏸️ 跳过推送")
    else:
        print("未配置远程仓库")
        print("如需推送，请先添加远程仓库:")
        print("git remote add origin <repository-url>")

if __name__ == "__main__":
    import os
    main()