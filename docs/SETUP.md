# DPA 智能知识引擎 - 环境配置指南

> **版本**: v4.0  
> **更新日期**: 2025年1月23日  
> **状态**: 基于dpa_gen conda环境的生产就绪配置

## 1. 环境要求

### 1.1 系统要求
- **操作系统**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python版本**: 3.11.5 (通过conda管理)
- **内存**: 最小8GB，推荐16GB+
- **存储**: 最小20GB可用空间
- **网络**: 稳定的互联网连接（用于AI API调用）

### 1.2 外部服务依赖
- **数据库服务器**: rtx4080:5432 (PostgreSQL)
- **向量数据库**: rtx4080:6333 (Qdrant)
- **图数据库**: rtx4080:7687 (Neo4j)
- **缓存服务**: rtx4080:6379 (Redis)

## 2. 快速开始 (推荐)

### 2.1 克隆项目
```bash
git clone <repository-url>
cd DPA
```

### 2.2 创建conda环境
```bash
# 使用environment.yml文件创建环境
conda env create -f environment.yml

# 激活环境
conda activate dpa_gen

# 验证环境
python --version  # 应显示 Python 3.11.5
```

### 2.3 配置环境变量
```bash
# 复制环境变量模板
cp env.template .env

# 编辑.env文件，配置以下关键参数：
# - 数据库连接信息 (rtx4080服务器)
# - AI API密钥 (OpenAI, Anthropic, Cohere等)
# - LangSmith监控配置
```

### 2.4 验证配置
```bash
# 运行配置测试
python scripts/test_config.py

# 运行组件测试
python scripts/test_components.py

# 查看测试报告
python scripts/test_report.py
```

### 2.5 启动开发服务器
```bash
# 使用开发脚本启动
./scripts/dev_setup.sh

# 或手动启动
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. 详细安装步骤

### 3.1 Conda环境管理

#### 创建环境 (使用environment.yml)
```bash
# 创建名为dpa_gen的环境
conda env create -f environment.yml -n dpa_gen

# 激活环境
conda activate dpa_gen

# 验证安装
pip list | grep -E "(langchain|fastapi|pydantic)"
```

#### 手动创建环境 (备选方案)
```bash
# 创建基础环境
conda create -n dpa_gen python=3.11.5 -y
conda activate dpa_gen

# 安装核心依赖
pip install -r requirements.txt

# 验证安装
python -c "import langchain, fastapi, pydantic; print('核心依赖安装成功')"
```

### 3.2 数据库连接配置

#### PostgreSQL连接测试
```bash
# 测试数据库连接
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='rtx4080',
        port=5432,
        database='dpa_dev',
        user='dpa_user',
        password='dpa_password'
    )
    print('PostgreSQL连接成功')
    conn.close()
except Exception as e:
    print(f'PostgreSQL连接失败: {e}')
"
```

#### Qdrant连接测试
```bash
# 测试向量数据库连接
python -c "
from qdrant_client import QdrantClient
try:
    client = QdrantClient(url='http://rtx4080:6333')
    print('Qdrant连接成功')
except Exception as e:
    print(f'Qdrant连接失败: {e}')
"
```

### 3.3 AI API配置

#### 配置API密钥
```bash
# 在.env文件中配置以下密钥：
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# LangSmith监控
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=dpa-development
```

#### 测试API连接
```bash
# 测试OpenAI API
python -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
try:
    response = client.models.list()
    print('OpenAI API连接成功')
except Exception as e:
    print(f'OpenAI API连接失败: {e}')
"
```

## 4. 开发工具配置

### 4.1 代码质量工具
```bash
# 代码格式化
ruff format .

# 代码检查
ruff check . --fix

# 类型检查
mypy src/ --strict

# 安全扫描
bandit -r src/ -f json -o security-report.json
```

### 4.2 测试框架
```bash
# 运行所有测试
pytest -v --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_basic.py -v

# 运行集成测试
pytest tests/test_integration.py -v
```

### 4.3 数据库迁移
```bash
# 初始化迁移
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "初始化数据库"

# 应用迁移
alembic upgrade head

# 查看迁移历史
alembic history
```

## 5. 故障排除

### 5.1 常见问题

#### Python版本问题
```bash
# 问题：Python版本不匹配
# 解决：确保使用Python 3.11.5
conda activate dpa_gen
python --version

# 如果版本不对，重新创建环境
conda remove -n dpa_gen --all
conda env create -f environment.yml
```

#### 依赖包冲突
```bash
# 问题：包版本冲突
# 解决：清理并重新安装
pip cache purge
pip uninstall -y langchain langchain-community langchain-core langchain-openai
pip install -r requirements.txt
```

#### 数据库连接问题
```bash
# 问题：无法连接到rtx4080服务器
# 解决：检查网络和防火墙设置
ping rtx4080
telnet rtx4080 5432

# 检查.env文件中的连接信息
cat .env | grep DATABASE_URL
```

#### LangChain版本兼容性
```bash
# 问题：LangChain版本不兼容
# 解决：确保使用指定版本
pip install langchain==0.3.26 langchain-community==0.3.26 langchain-core==0.3.66
```

### 5.2 日志调试
```bash
# 启用调试日志
export DEBUG=true
export LOG_LEVEL=DEBUG

# 查看应用日志
tail -f data/logs/app.log

# 查看错误日志
tail -f data/logs/error.log
```

### 5.3 性能调优
```bash
# 检查系统资源
htop
free -h
df -h

# 监控数据库连接
python -c "
from src.database.postgresql import get_db_stats
print(get_db_stats())
"
```

## 6. 生产部署

### 6.1 Docker部署
```bash
# 构建镜像
docker-compose -f docker-compose.dev.yml build

# 启动服务
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f api
```

### 6.2 性能优化
```bash
# 启用生产模式
export ENVIRONMENT=production
export DEBUG=false

# 使用Gunicorn启动
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 7. 验证清单

### 7.1 环境验证
- [ ] conda环境 `dpa_gen` 创建成功
- [ ] Python版本为 3.11.5
- [ ] 所有依赖包安装成功
- [ ] .env文件配置完成

### 7.2 服务连接验证
- [ ] PostgreSQL连接成功 (rtx4080:5432)
- [ ] Qdrant连接成功 (rtx4080:6333)
- [ ] Neo4j连接成功 (rtx4080:7687)
- [ ] Redis连接成功 (rtx4080:6379)

### 7.3 API验证
- [ ] OpenAI API连接成功
- [ ] Anthropic API连接成功
- [ ] LangSmith监控配置成功

### 7.4 功能验证
- [ ] 配置系统正常加载
- [ ] 数据模型正常工作
- [ ] 文档解析器正常工作
- [ ] 文档分块系统正常
- [ ] 向量化系统正常

### 7.5 开发工具验证
- [ ] 代码格式化工具正常
- [ ] 类型检查工具正常
- [ ] 测试框架正常
- [ ] 数据库迁移正常

## 8. 支持与帮助

### 8.1 文档资源
- [PRD产品需求文档](./PRD.md)
- [TECH_SPEC技术规格](./TECH_SPEC.md)
- [开发计划](./DEVELOPMENT_PLAN.md)

### 8.2 常用命令速查
```bash
# 环境管理
conda activate dpa_gen
conda deactivate

# 开发服务器
uvicorn src.api.main:app --reload
./scripts/dev_setup.sh

# 测试
pytest -v
python scripts/test_config.py

# 代码质量
ruff format .
ruff check . --fix
mypy src/ --strict

# 数据库
alembic upgrade head
python scripts/setup_databases.py
```

### 8.3 性能基准
- **启动时间**: < 10秒
- **配置加载**: < 2秒
- **数据库连接**: < 1秒
- **API响应**: < 100ms (健康检查)
- **内存使用**: < 2GB (空载) 