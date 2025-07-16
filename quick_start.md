# 🚀 DPA 快速启动指南

## 启动步骤

### 1. 激活Conda环境
```bash
# 激活conda环境
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen
```

### 2. 启动后端服务
```bash
# 切换到项目目录
cd /Users/mdwong001/Desktop/code/rag/DPA

# 启动后端服务
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
```

### 3. 启动前端服务 (新终端窗口)
```bash
# 切换到前端目录
cd /Users/mdwong001/Desktop/code/rag/DPA/frontend

# 启动前端服务
npm run dev
```

### 4. 验证服务状态
```bash
# 检查后端服务
curl http://localhost:8200/api/v1/health

# 检查前端服务
curl http://localhost:8230
```

## 快速启动命令

### 一键启动后端
```bash
cd /Users/mdwong001/Desktop/code/rag/DPA && eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)" && conda activate dpa_gen && uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
```

### 一键启动前端
```bash
cd /Users/mdwong001/Desktop/code/rag/DPA/frontend && npm run dev
```

## 访问地址

- **后端API**: http://localhost:8200
- **API文档**: http://localhost:8200/docs
- **前端应用**: http://localhost:8230
- **AAG页面**: http://localhost:8230/aag

## 测试工具

启动服务后，可以使用以下测试工具：

### 1. 浏览器自动化测试
```bash
open test_browser_simple.html
```

### 2. WebSocket诊断工具
```bash
open websocket_diagnostic.html
```

### 3. Python服务测试
```bash
python test_services.py
```

## 常见问题

### 问题1: Conda环境未激活
```bash
# 解决方法
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen
```

### 问题2: 端口被占用
```bash
# 检查端口占用
lsof -i :8200  # 后端端口
lsof -i :8230  # 前端端口

# 杀死占用进程
kill -9 <PID>
```

### 问题3: 前端依赖缺失
```bash
cd frontend
npm install
```

### 问题4: 数据库连接失败
```bash
# 检查数据库配置
cat .env

# 确保数据库服务运行
# PostgreSQL, Qdrant, Neo4j等
```

## 启动顺序

1. ✅ 激活conda环境
2. ✅ 启动后端服务 (等待服务就绪)
3. ✅ 启动前端服务 (等待服务就绪)
4. ✅ 验证服务状态
5. ✅ 运行测试工具
6. ✅ 访问AAG页面

## 成功指示

当看到以下输出时，说明服务启动成功：

### 后端服务成功启动
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8200 (Press CTRL+C to quit)
```

### 前端服务成功启动
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:8230
  - Network:      http://0.0.0.0:8230

 ✓ Ready in 3.2s
```

## 下一步

服务启动后，您可以：
1. 访问 http://localhost:8230/aag 使用AAG功能
2. 使用测试工具验证功能
3. 上传文档并测试摘要生成
4. 测试查看结果功能

---

🎯 **立即开始**: 请在终端中运行上述命令来启动DPA服务！