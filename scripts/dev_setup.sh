#!/bin/bash

# ==========================================
# DPA项目开发环境快速设置脚本
# ==========================================

set -e  # 遇到错误时退出

echo "🚀 开始设置DPA开发环境..."

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

# 检查必要工具
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3未安装，请先安装Python 3.11+"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js 18+"
        exit 1
    fi
    
    # 检查pnpm
    if ! command -v pnpm &> /dev/null; then
        log_warning "pnpm未安装，正在安装..."
        npm install -g pnpm
    fi
    
    # 检查conda
    if ! command -v conda &> /dev/null; then
        log_warning "Conda未安装，将使用pip进行Python包管理"
    fi
    
    log_success "系统要求检查完成"
}

# 创建.env文件
setup_env_file() {
    log_info "设置环境配置文件..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.template" ]; then
            cp env.template .env
            log_success "已从模板创建.env文件"
            log_warning "请编辑.env文件，填写您的数据库连接信息"
        else
            log_error "找不到env.template文件"
            exit 1
        fi
    else
        log_info ".env文件已存在，跳过创建"
    fi
}

# 设置Python环境
setup_python_env() {
    log_info "设置Python环境..."
    
    # 尝试使用conda创建环境
    if command -v conda &> /dev/null; then
        log_info "使用conda创建虚拟环境..."
        
        # 检查环境是否已存在
        if conda env list | grep -q "dpa-dev"; then
            log_info "conda环境dpa-dev已存在"
        else
            conda create -n dpa-dev python=3.11 -y
            log_success "conda环境dpa-dev创建完成"
        fi
        
        log_info "激活conda环境并安装依赖..."
        eval "$(conda shell.bash hook)"
        conda activate dpa-dev
        
        # 安装核心依赖
        conda install -c conda-forge numpy pandas fastapi uvicorn redis-py psycopg2 -y
        
        # 安装其他依赖
        pip install --upgrade pip
        pip install -r requirements.txt
        
    else
        log_info "使用pip创建虚拟环境..."
        
        # 创建虚拟环境
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            log_success "Python虚拟环境创建完成"
        fi
        
        # 激活虚拟环境
        source venv/bin/activate
        
        # 安装依赖
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    log_success "Python环境设置完成"
}

# 设置前端环境
setup_frontend_env() {
    log_info "设置前端环境..."
    
    # 检查frontend目录
    if [ ! -d "frontend" ]; then
        log_info "创建Next.js前端项目..."
        pnpm create next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
        cd frontend
        
        # 安装额外依赖
        pnpm add @tanstack/react-query lucide-react @radix-ui/react-dialog @radix-ui/react-dropdown-menu
        pnpm add -D @types/node
        
        # 初始化shadcn/ui
        pnpm dlx shadcn-ui@latest init -d
        
        cd ..
        log_success "前端项目创建完成"
    else
        log_info "前端目录已存在，安装依赖..."
        cd frontend
        pnpm install
        cd ..
        log_success "前端依赖安装完成"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建项目目录结构..."
    
    directories=(
        "data/uploads"
        "data/processed" 
        "data/cache"
        "data/logs"
        "data/vectors"
        "backend"
        "scripts"
        "tests/unit"
        "tests/integration"
        "tests/e2e"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    log_success "目录结构创建完成"
}

# 初始化数据库
init_databases() {
    log_info "检查数据库配置..."
    
    if [ -f ".env" ]; then
        # 检查.env文件中是否有数据库配置
        if grep -q "your_" .env; then
            log_warning "检测到.env文件中还有未配置的占位符"
            log_warning "请先配置数据库连接信息，然后运行: python scripts/setup_databases.py"
            return
        fi
        
        log_info "尝试初始化数据库..."
        python scripts/setup_databases.py
    else
        log_warning "未找到.env文件，跳过数据库初始化"
    fi
}

# 运行测试
run_tests() {
    log_info "运行基础测试..."
    
    # Python测试
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short || log_warning "部分Python测试失败"
    else
        log_warning "pytest未安装，跳过Python测试"
    fi
    
    # 前端测试
    if [ -d "frontend" ]; then
        cd frontend
        if [ -f "package.json" ] && grep -q "test" package.json; then
            pnpm test || log_warning "部分前端测试失败"
        fi
        cd ..
    fi
    
    log_success "测试完成"
}

# 显示启动说明
show_startup_instructions() {
    log_success "🎉 开发环境设置完成！"
    echo
    echo "📋 接下来的步骤："
    echo "1. 编辑 .env 文件，填写您的数据库连接信息"
    echo "2. 运行数据库初始化: python scripts/setup_databases.py"
    echo "3. 启动后端服务: uvicorn src.api.main:app --reload"
    echo "4. 启动前端服务: cd frontend && pnpm dev"
    echo
    echo "🔗 访问地址："
    echo "  - 前端: http://localhost:3000"
    echo "  - 后端API: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo
    echo "📚 有用的命令："
    echo "  - 查看日志: tail -f data/logs/dpa.log"
    echo "  - 运行测试: pytest tests/"
    echo "  - 代码格式化: ruff format ."
    echo "  - 类型检查: mypy src/"
}

# 主函数
main() {
    log_info "DPA深度研究知识引擎 - 开发环境设置"
    echo "========================================"
    
    check_requirements
    create_directories
    setup_env_file
    setup_python_env
    setup_frontend_env
    init_databases
    run_tests
    show_startup_instructions
}

# 运行主函数
main "$@" 