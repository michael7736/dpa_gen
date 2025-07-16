#!/bin/bash

echo "=========================================="
echo "DPA 对话历史功能集成测试"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端服务
echo -e "\n${YELLOW}1. 检查后端服务状态...${NC}"
if curl -s http://localhost:8200/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务正在运行${NC}"
else
    echo -e "${RED}❌ 后端服务未运行${NC}"
    echo "请先启动后端服务："
    echo "  cd /Users/mdwong001/Desktop/code/rag/DPA"
    echo "  source /Users/mdwong001/mambaforge/bin/activate dpa_gen"
    echo "  uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload"
    exit 1
fi

# 激活conda环境
echo -e "\n${YELLOW}2. 激活conda环境...${NC}"
source /Users/mdwong001/mambaforge/bin/activate dpa_gen

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:/Users/mdwong001/Desktop/code/rag/DPA"

# 运行集成测试
echo -e "\n${YELLOW}3. 运行集成测试...${NC}"
cd /Users/mdwong001/Desktop/code/rag/DPA
python scripts/test_integration.py

# 检查测试结果
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 所有测试通过！${NC}"
else
    echo -e "\n${RED}❌ 部分测试失败，请查看错误信息${NC}"
fi

echo -e "\n=========================================="