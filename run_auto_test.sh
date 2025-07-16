#!/bin/zsh

# DPA自动化测试启动脚本

echo "🚀 DPA自动化集成测试启动脚本"
echo "================================"

# 切换到项目目录
cd /Users/mdwong001/Desktop/code/rag/DPA

# 激活conda环境
echo "🐍 激活conda环境..."
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen

# 检查环境
echo "📍 当前环境: $(conda info --envs | grep '*' | awk '{print $1}')"
echo "📍 Python路径: $(which python)"

# 运行自动化测试
echo "🧪 开始运行自动化测试..."
python auto_test_system.py