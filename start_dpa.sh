#!/bin/bash

# DPA 自动化启动脚本
# 使用方法: ./start_dpa.sh

set -e  # 遇到错误时退出

echo "🚀 DPA 自动化启动脚本"
echo "===================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查conda
    if ! command -v conda &> /dev/null; then
        log_error "Conda未安装或未配置"
        exit 1
    fi
    
    # 检查node
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 激活conda环境
activate_conda() {
    log_info "激活conda环境..."
    
    # 初始化conda
    eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.bash hook)"
    
    # 激活环境
    conda activate dpa_gen
    
    if [ $? -eq 0 ]; then
        log_success "Conda环境已激活"
    else
        log_error "无法激活conda环境dpa_gen"
        exit 1
    fi
}

# 检查端口
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "${service}端口${port}已被占用"
        
        # 询问是否杀死进程
        read -p "是否杀死占用进程？(y/n): " kill_process
        if [ "$kill_process" = "y" ]; then
            pkill -f ":$port" || true
            sleep 2
            log_success "已杀死占用端口${port}的进程"
        else
            log_error "端口${port}被占用，无法启动${service}"
            exit 1
        fi
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 检查端口
    check_port 8200 "后端服务"
    
    # 切换到项目目录
    cd /Users/mdwong001/Desktop/code/rag/DPA
    
    # 检查主文件
    if [ ! -f "src/api/main.py" ]; then
        log_error "未找到后端主文件src/api/main.py"
        exit 1
    fi
    
    # 启动服务
    log_info "启动uvicorn服务器..."
    nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo $BACKEND_PID > backend.pid
    
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待服务就绪
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1; then
            log_success "后端服务已就绪"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    log_error "后端服务启动超时"
    log_info "查看日志: tail -f backend.log"
    exit 1
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    # 检查端口
    check_port 8230 "前端服务"
    
    # 切换到前端目录
    cd /Users/mdwong001/Desktop/code/rag/DPA/frontend
    
    # 检查package.json
    if [ ! -f "package.json" ]; then
        log_error "未找到前端配置文件package.json"
        exit 1
    fi
    
    # 检查依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi
    
    # 启动服务
    log_info "启动Next.js开发服务器..."
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    echo $FRONTEND_PID > ../frontend.pid
    
    log_success "前端服务已启动 (PID: $FRONTEND_PID)"
    
    # 等待服务就绪
    log_info "等待前端服务启动..."
    for i in {1..60}; do
        if curl -s http://localhost:8230 > /dev/null 2>&1; then
            log_success "前端服务已就绪"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    log_error "前端服务启动超时"
    log_info "查看日志: tail -f frontend.log"
    exit 1
}

# 验证服务
verify_services() {
    log_info "验证服务状态..."
    
    # 检查后端
    if curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1; then
        log_success "后端服务: ✅ 正常"
    else
        log_error "后端服务: ❌ 异常"
        return 1
    fi
    
    # 检查前端
    if curl -s http://localhost:8230 > /dev/null 2>&1; then
        log_success "前端服务: ✅ 正常"
    else
        log_error "前端服务: ❌ 异常"
        return 1
    fi
    
    log_success "所有服务验证通过"
}

# 显示服务信息
show_service_info() {
    echo ""
    echo "🎉 DPA服务启动成功！"
    echo "===================="
    echo ""
    echo "📊 服务信息:"
    echo "   后端服务: http://localhost:8200"
    echo "   API文档:  http://localhost:8200/docs"
    echo "   前端服务: http://localhost:8230"
    echo "   AAG页面:  http://localhost:8230/aag"
    echo ""
    echo "🔍 测试工具:"
    echo "   浏览器测试: open test_browser_simple.html"
    echo "   WebSocket诊断: open websocket_diagnostic.html"
    echo "   Python测试: python test_services.py"
    echo ""
    echo "📋 日志文件:"
    echo "   后端日志: tail -f backend.log"
    echo "   前端日志: tail -f frontend.log"
    echo ""
    echo "🛑 停止服务:"
    echo "   ./stop_dpa.sh"
    echo ""
}

# 创建停止脚本
create_stop_script() {
    cat > stop_dpa.sh << 'EOF'
#!/bin/bash

echo "🛑 停止DPA服务..."

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)"
        kill $BACKEND_PID
        rm backend.pid
    fi
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID
        rm frontend.pid
    fi
fi

# 备用方法：按端口杀死进程
pkill -f "uvicorn.*8200" || true
pkill -f "next.*8230" || true

echo "✅ DPA服务已停止"
EOF

    chmod +x stop_dpa.sh
    log_success "停止脚本已创建: stop_dpa.sh"
}

# 主函数
main() {
    # 检查依赖
    check_dependencies
    
    # 激活conda环境
    activate_conda
    
    # 启动后端服务
    start_backend
    
    # 启动前端服务
    start_frontend
    
    # 验证服务
    verify_services
    
    # 创建停止脚本
    create_stop_script
    
    # 显示服务信息
    show_service_info
    
    log_success "DPA启动完成！"
}

# 捕获中断信号
trap 'log_warning "启动被中断"; exit 1' INT

# 运行主函数
main "$@"