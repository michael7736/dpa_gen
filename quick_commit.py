#!/usr/bin/env python3
import subprocess
import os

# 切换到项目目录
os.chdir("/Users/mdwong001/Desktop/code/rag/DPA")

print("🔧 执行Git提交...")

# 1. 添加所有更改
print("1. 添加所有更改...")
subprocess.run(["git", "add", "."], check=True)
print("✅ 文件添加完成")

# 2. 创建提交
print("2. 创建提交...")
commit_msg = """fix: 修复DPA系统核心功能问题并添加自动化测试

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

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

# 写入临时文件
with open("/tmp/commit_msg.txt", "w") as f:
    f.write(commit_msg)

subprocess.run(["git", "commit", "-F", "/tmp/commit_msg.txt"], check=True)
print("✅ 提交创建完成")

# 3. 检查远程仓库并推送
print("3. 检查远程仓库...")
result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
if result.stdout.strip():
    print("发现远程仓库，开始推送...")
    try:
        subprocess.run(["git", "push"], check=True)
        print("✅ 推送成功!")
    except subprocess.CalledProcessError:
        print("推送失败，尝试设置上游分支...")
        branch_result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        if branch_result.stdout.strip():
            branch_name = branch_result.stdout.strip()
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
            print("✅ 设置上游分支并推送成功!")
else:
    print("未配置远程仓库")

print("✅ Git操作完成!")