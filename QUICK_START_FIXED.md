# 🚀 DPA 快速启动指南

## 问题已修复 ✅
- ✅ Neo4j数据库配置已修复：`NEO4J_DATABASE=neo4j`
- ✅ 现在可以正常启动服务

## 立即启动服务

### 方法1：手动启动（推荐）

#### 终端1 - 启动后端
```bash
# 切换到项目目录
cd /Users/mdwong001/Desktop/code/rag/DPA

# 激活conda环境
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen

# 启动后端服务
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
```

#### 终端2 - 启动前端
```bash
# 切换到前端目录
cd /Users/mdwong001/Desktop/code/rag/DPA/frontend

# 启动前端服务
npm run dev
```

### 方法2：使用Python脚本
```bash
# 直接运行启动脚本
/Users/mdwong001/miniconda3/envs/dpa_gen/bin/python start_services.py
```

### 方法3：使用Shell脚本
```bash
# 给脚本执行权限并运行
chmod +x start_dpa.sh
./start_dpa.sh
```

## 验证启动成功

### 检查服务状态
```bash
# 检查后端服务
curl http://localhost:8200/api/v1/health

# 检查前端服务  
curl http://localhost:8230
```

### 访问应用
- **后端API**: http://localhost:8200
- **API文档**: http://localhost:8200/docs
- **前端应用**: http://localhost:8230
- **AAG页面**: http://localhost:8230/aag

## 测试工具

### 浏览器自动化测试
```bash
# 打开测试工具
open test_browser_simple.html
```

### WebSocket诊断
```bash
# 打开WebSocket测试工具
open websocket_diagnostic.html
```

## 启动成功指示

### 后端服务启动成功
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8200 (Press CTRL+C to quit)
```

### 前端服务启动成功
```
▲ Next.js 14.x.x
- Local:        http://localhost:8230
- Network:      http://0.0.0.0:8230

✓ Ready in 3.2s
```

## 故障排除

### 1. 端口占用问题
```bash
# 查看端口占用
lsof -i :8200
lsof -i :8230

# 杀死占用进程
kill -9 <PID>
```

### 2. Conda环境问题
```bash
# 检查环境
conda info --envs

# 重新激活
conda deactivate
conda activate dpa_gen
```

### 3. 依赖问题
```bash
# 重新安装Python依赖
pip install -r requirements.txt

# 重新安装前端依赖
cd frontend
npm install
```

## 使用流程

1. **访问AAG页面**: http://localhost:8230/aag
2. **上传文档**: 拖拽或点击上传PDF文档
3. **选择处理选项**: 勾选需要的分析类型（摘要、索引等）
4. **等待处理完成**: 观察WebSocket实时进度
5. **查看结果**: 点击"查看结果"按钮
6. **AI问答**: 在聊天界面询问关于文档的问题

## 主要修复

1. **Neo4j数据库配置**：
   - 原：`NEO4J_DATABASE=dpa_graph`
   - 修复：`NEO4J_DATABASE=neo4j`

2. **ResultViewModal组件**：
   - 修复了属性传递问题
   - 添加了missing documentName属性

3. **WebSocket服务**：
   - 增强了错误处理和重连机制
   - 添加了优雅降级功能

---

🎯 **现在就开始使用DPA吧！所有问题都已修复。**