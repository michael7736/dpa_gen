# DPA 深度研究知识引擎 - 开发环境设置指南

## 📋 概述

本文档将指导您完成DPA项目的开发环境设置，包括数据库配置、依赖安装和项目启动。

## 🔧 系统要求

### 必需组件
- **Python 3.11+** - 后端开发语言
- **Node.js 18+** - 前端开发环境
- **pnpm** - 前端包管理器（推荐）

### 数据库要求（需要您手动部署）
- **PostgreSQL 15+** - 主数据库
- **Qdrant 1.8+** - 向量数据库
- **Neo4j 5.0+** - 图数据库
- **Redis 7+** - 缓存和消息队列

### 可选组件
- **Conda/Miniconda** - Python环境管理（推荐）
- **Docker** - 容器化部署

## 🚀 快速开始

### 方法一：自动设置脚本（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd DPA

# 运行自动设置脚本
./scripts/dev_setup.sh
```

### 方法二：手动设置

#### 1. 创建环境配置

```bash
# 复制环境配置模板
cp env.template .env

# 编辑配置文件，填写您的数据库信息
vim .env
```

#### 2. 设置Python环境

使用Conda（推荐）：
```bash
# 创建虚拟环境
conda create -n dpa-dev python=3.11
conda activate dpa-dev

# 安装核心依赖
conda install -c conda-forge numpy pandas fastapi uvicorn redis-py psycopg2

# 安装其他依赖
pip install --upgrade pip
pip install -r requirements.txt
```

使用pip：
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. 设置前端环境

```bash
# 安装pnpm（如果未安装）
npm install -g pnpm

# 创建Next.js项目（如果frontend目录不存在）
pnpm create next-app@latest frontend --typescript --tailwind --eslint

# 进入前端目录并安装依赖
cd frontend
pnpm install

# 安装UI组件库
pnpm add @tanstack/react-query lucide-react
pnpm dlx shadcn-ui@latest init

cd ..
```

#### 4. 初始化数据库

```bash
# 运行数据库初始化脚本
python scripts/setup_databases.py
```

## ⚙️ 环境配置详解

### .env 文件配置

复制 `env.template` 为 `.env` 并填写以下关键配置：

```bash
# 数据库配置
DATABASE_URL=postgresql://username:password@host:5432/database
QDRANT_URL=http://host:6333
NEO4J_URL=bolt://host:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
REDIS_URL=redis://host:6379

# AI模型配置
OPENROUTER_API_KEY=your_api_key

# 安全配置
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### 数据库连接信息填写示例

#### PostgreSQL
```bash
# 本地部署
DATABASE_URL=postgresql://dpa_user:dpa_password@localhost:5432/dpa_dev

# 云服务（如AWS RDS）
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/dpa_prod
```

#### Qdrant
```bash
# 本地部署
QDRANT_URL=http://localhost:6333

# 云服务
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_api_key
```

#### Neo4j
```bash
# 本地部署
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Neo4j AuraDB
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
```

#### Redis
```bash
# 本地部署
REDIS_URL=redis://localhost:6379

# 云服务（如Redis Cloud）
REDIS_URL=redis://username:password@host:port
```

## 🏃‍♂️ 启动项目

### 启动后端服务

```bash
# 激活Python环境
conda activate dpa-dev  # 或 source venv/bin/activate

# 启动FastAPI服务
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
pnpm dev
```

### 启动异步任务处理器（可选）

```bash
# 启动Celery Worker
celery -A src.celery worker --loglevel=info
```

## 🔗 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **API交互文档**: http://localhost:8000/redoc

## 🧪 运行测试

```bash
# Python测试
pytest tests/ -v --cov=src

# 前端测试
cd frontend
pnpm test

# 代码质量检查
ruff check . --fix
ruff format .
mypy src/
```

## 📁 项目结构

```
DPA/
├── src/                    # 后端源码
│   ├── api/               # API路由
│   ├── config/            # 配置管理
│   ├── core/              # 核心业务逻辑
│   ├── database/          # 数据库连接
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   └── utils/             # 工具函数
├── frontend/              # 前端源码
├── tests/                 # 测试文件
├── scripts/               # 脚本文件
├── data/                  # 数据目录
├── docs/                  # 文档
├── .env                   # 环境配置（需要创建）
├── env.template           # 环境配置模板
├── requirements.txt       # Python依赖
└── environment.yml        # Conda环境配置
```

## 🐛 常见问题

### 1. 数据库连接失败

**问题**: `connection to server failed`

**解决方案**:
- 检查数据库服务是否启动
- 验证连接信息（主机、端口、用户名、密码）
- 确认防火墙设置
- 检查网络连通性

### 2. Python依赖安装失败

**问题**: `pip install` 报错

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 如果是M1 Mac，可能需要特殊处理
conda install -c conda-forge psycopg2
```

### 3. 前端启动失败

**问题**: `pnpm dev` 报错

**解决方案**:
```bash
# 清理缓存
pnpm store prune

# 重新安装依赖
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 检查Node.js版本
node --version  # 应该是18+
```

### 4. 环境变量未生效

**问题**: 配置读取错误

**解决方案**:
- 确认 `.env` 文件在项目根目录
- 检查环境变量格式（无空格、正确的等号）
- 重启应用服务

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`tail -f data/logs/dpa.log`
2. 运行诊断脚本：`python scripts/setup_databases.py`
3. 检查系统要求是否满足
4. 参考错误日志进行排查

## 🎯 下一步

环境设置完成后，您可以：

1. 查看 [API文档](http://localhost:8000/docs) 了解接口
2. 阅读 [开发指南](./DEVELOPMENT.md) 了解开发流程
3. 参考 [部署指南](./DEPLOYMENT.md) 进行生产部署
4. 查看 [贡献指南](./CONTRIBUTING.md) 参与项目开发

---

**祝您开发愉快！** 🚀 