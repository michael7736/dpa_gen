#!/bin/bash

# DPA Git提交脚本

echo "🔧 DPA系统Git提交"
echo "=================="

# 切换到项目目录
cd /Users/mdwong001/Desktop/code/rag/DPA

# 查看状态
echo "📋 当前Git状态:"
git status --short

# 添加所有更改
echo "➕ 添加所有更改..."
git add .

# 创建提交
echo "💾 创建提交..."
git commit -m "fix: 修复DPA系统核心功能问题并添加自动化测试

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

Co-Authored-By: Claude <noreply@anthropic.com>"

# 查看提交结果
echo "✅ 提交完成"
git log --oneline -1

# 检查远程仓库
echo "🔍 检查远程仓库..."
git remote -v

# 推送到远程仓库
echo "🚀 推送到远程仓库..."
git push

echo "✅ 所有操作完成!"