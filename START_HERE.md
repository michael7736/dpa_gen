# 🚀 DPA 服务启动指南

## 立即开始

### 方法1: 自动化启动脚本 (推荐)

#### macOS/Linux:
```bash
# 1. 给脚本执行权限
chmod +x start_dpa.sh

# 2. 运行启动脚本
./start_dpa.sh
```

#### Windows:
```batch
# 双击运行
start_dpa.bat
```

### 方法2: 手动启动

#### 步骤1: 激活环境
```bash
# 激活conda环境
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)"
conda activate dpa_gen
```

#### 步骤2: 启动后端 (终端1)
```bash
cd /Users/mdwong001/Desktop/code/rag/DPA
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
```

#### 步骤3: 启动前端 (终端2)
```bash
cd /Users/mdwong001/Desktop/code/rag/DPA/frontend
npm run dev
```

### 方法3: 检查和启动工具
```bash
# 检查服务状态并自动启动
python check_services.py
```

## 验证启动

### 检查服务状态
```bash
# 后端服务
curl http://localhost:8200/api/v1/health

# 前端服务
curl http://localhost:8230
```

### 访问地址
- **后端API**: http://localhost:8200
- **API文档**: http://localhost:8200/docs
- **前端应用**: http://localhost:8230
- **AAG页面**: http://localhost:8230/aag

## 运行测试

### 浏览器自动化测试
```bash
# 打开测试工具
open test_browser_simple.html

# 或使用Python启动器
python test_with_puppeteer.py
```

### WebSocket诊断
```bash
# 打开WebSocket测试工具
open websocket_diagnostic.html
```

### Python服务测试
```bash
# 运行Python测试脚本
python test_services.py
```

## 成功指示

当您看到以下信息时，说明服务启动成功：

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

## 测试流程

1. **服务状态检查** ✅
   - 后端健康检查
   - 前端访问测试
   - WebSocket连接测试

2. **API端点测试** ✅
   - 健康检查API
   - 文档管理API
   - 项目管理API

3. **前端功能测试** ✅
   - AAG页面加载
   - 文档上传功能
   - 摘要生成功能
   - 结果查看功能

4. **端到端测试** ✅
   - 完整的文档处理流程
   - WebSocket实时通知
   - 错误处理和恢复

## 故障排除

### 常见问题

#### 1. Conda环境问题
```bash
# 重新激活环境
conda deactivate
conda activate dpa_gen

# 检查环境
conda info --envs
```

#### 2. 端口被占用
```bash
# 查看端口占用
lsof -i :8200  # 后端端口
lsof -i :8230  # 前端端口

# 杀死占用进程
kill -9 <PID>
```

#### 3. 依赖缺失
```bash
# 重新安装Python依赖
pip install -r requirements.txt

# 重新安装前端依赖
cd frontend
npm install
```

#### 4. 数据库连接问题
```bash
# 检查环境变量
cat .env

# 检查数据库服务
# 确保PostgreSQL, Qdrant, Neo4j等服务正在运行
```

## 停止服务

### 自动停止
```bash
# 如果使用了启动脚本
./stop_dpa.sh
```

### 手动停止
```bash
# 在启动服务的终端中按 Ctrl+C
# 或者杀死进程
pkill -f "uvicorn.*8200"
pkill -f "next.*8230"
```

## 下一步

服务启动成功后，您可以：

1. **访问AAG页面**: http://localhost:8230/aag
2. **上传测试文档**: 使用拖拽或点击上传
3. **生成摘要**: 勾选摘要选项并上传
4. **查看结果**: 点击"查看结果"按钮
5. **测试问答**: 在AI助手中提问

## 完整测试检查清单

- [ ] 后端服务启动成功
- [ ] 前端服务启动成功
- [ ] API健康检查通过
- [ ] AAG页面加载正常
- [ ] 文档上传功能正常
- [ ] 摘要生成功能正常
- [ ] 结果查看功能正常
- [ ] WebSocket连接正常
- [ ] 错误处理正常

---

🎯 **快速启动**: 运行 `./start_dpa.sh` 开始使用DPA！