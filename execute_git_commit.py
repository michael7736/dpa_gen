#!/usr/bin/env python3
"""
执行Git提交的Python脚本
"""

import subprocess
import os
import sys

def execute_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="/Users/mdwong001/Desktop/code/rag/DPA")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔧 DPA Git提交脚本")
    print("="*40)
    
    # 1. 检查Git状态
    print("📋 检查Git状态...")
    success, stdout, stderr = execute_command("git status --porcelain")
    if success:
        if stdout.strip():
            print("发现以下更改:")
            print(stdout)
        else:
            print("没有更改需要提交")
            return
    else:
        print(f"检查状态失败: {stderr}")
        return
    
    # 2. 添加所有文件
    print("\n➕ 添加所有更改...")
    success, stdout, stderr = execute_command("git add .")
    if success:
        print("✅ 文件添加成功")
    else:
        print(f"❌ 添加文件失败: {stderr}")
        return
    
    # 3. 创建提交
    print("\n💾 创建提交...")
    
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
    
    # 使用临时文件保存提交消息
    with open("/tmp/commit_message.txt", "w") as f:
        f.write(commit_message)
    
    success, stdout, stderr = execute_command("git commit -F /tmp/commit_message.txt")
    if success:
        print("✅ 提交成功!")
        print(stdout)
    else:
        print(f"❌ 提交失败: {stderr}")
        return
    
    # 4. 检查远程仓库
    print("\n🔍 检查远程仓库...")
    success, stdout, stderr = execute_command("git remote -v")
    if success and stdout.strip():
        print("远程仓库:")
        print(stdout)
        
        # 5. 推送到远程仓库
        print("\n🚀 推送到远程仓库...")
        success, stdout, stderr = execute_command("git push")
        if success:
            print("✅ 推送成功!")
            print(stdout)
        else:
            print(f"❌ 推送失败: {stderr}")
            print("可能的原因:")
            print("- 网络连接问题")
            print("- 认证问题")
            print("- 分支保护规则")
            print("- 需要先设置上游分支")
            
            # 尝试设置上游分支
            current_branch_cmd = "git branch --show-current"
            success2, branch_name, _ = execute_command(current_branch_cmd)
            if success2 and branch_name.strip():
                print(f"\n尝试设置上游分支: {branch_name.strip()}")
                success3, stdout3, stderr3 = execute_command(f"git push -u origin {branch_name.strip()}")
                if success3:
                    print("✅ 设置上游分支并推送成功!")
                    print(stdout3)
                else:
                    print(f"❌ 设置上游分支失败: {stderr3}")
    else:
        print("未配置远程仓库")
        print("请先添加远程仓库:")
        print("git remote add origin <repository-url>")
    
    # 6. 显示最终状态
    print("\n📊 最终状态:")
    success, stdout, stderr = execute_command("git log --oneline -3")
    if success:
        print("最近的提交:")
        print(stdout)
    
    print("\n✅ Git操作完成!")

if __name__ == "__main__":
    main()