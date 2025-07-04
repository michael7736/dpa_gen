#!/bin/bash
# DPA部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印函数
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查必要工具
check_requirements() {
    info "检查部署环境..."
    
    command -v docker >/dev/null 2>&1 || error "Docker未安装"
    command -v docker-compose >/dev/null 2>&1 || error "Docker Compose未安装"
    
    # 检查Docker服务
    docker info >/dev/null 2>&1 || error "Docker服务未运行"
    
    info "环境检查通过"
}

# 加载环境变量
load_env() {
    if [ -f .env ]; then
        info "加载环境变量..."
        export $(grep -v '^#' .env | xargs)
    else
        error ".env文件不存在"
    fi
}

# 构建镜像
build_image() {
    info "构建Docker镜像..."
    
    # 使用BuildKit加速构建
    export DOCKER_BUILDKIT=1
    
    docker build \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD) \
        -t dpa:latest \
        -t dpa:$(git describe --tags --always) \
        .
        
    info "镜像构建完成"
}

# 部署服务
deploy_services() {
    local env=$1
    info "部署服务 (环境: $env)..."
    
    case $env in
        "dev")
            docker-compose up -d
            ;;
        "prod")
            docker-compose -f docker-compose.prod.yml up -d
            ;;
        *)
            error "未知环境: $env"
            ;;
    esac
    
    info "等待服务启动..."
    sleep 10
    
    # 健康检查
    health_check
}

# 健康检查
health_check() {
    info "执行健康检查..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            info "服务健康检查通过"
            return 0
        fi
        
        attempt=$((attempt + 1))
        warn "健康检查失败，重试 $attempt/$max_attempts..."
        sleep 2
    done
    
    error "服务启动失败"
}

# 查看日志
show_logs() {
    docker-compose logs -f --tail=100
}

# 停止服务
stop_services() {
    info "停止服务..."
    docker-compose down
}

# 清理资源
cleanup() {
    warn "清理Docker资源..."
    docker system prune -f
    docker volume prune -f
}

# 备份数据
backup_data() {
    info "备份数据..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $backup_dir
    
    # 备份上传的文件
    cp -r data/uploads $backup_dir/
    
    # 备份日志
    cp -r logs $backup_dir/
    
    # 创建备份信息
    echo "Backup created at $(date)" > $backup_dir/info.txt
    echo "Git commit: $(git rev-parse HEAD)" >> $backup_dir/info.txt
    
    info "备份完成: $backup_dir"
}

# 主菜单
show_menu() {
    echo "======================================"
    echo "        DPA部署管理工具"
    echo "======================================"
    echo "1. 部署开发环境"
    echo "2. 部署生产环境"
    echo "3. 查看服务日志"
    echo "4. 停止所有服务"
    echo "5. 健康检查"
    echo "6. 备份数据"
    echo "7. 清理资源"
    echo "8. 退出"
    echo "======================================"
}

# 主函数
main() {
    check_requirements
    load_env
    
    if [ $# -eq 0 ]; then
        # 交互模式
        while true; do
            show_menu
            read -p "请选择操作 [1-8]: " choice
            
            case $choice in
                1)
                    build_image
                    deploy_services "dev"
                    ;;
                2)
                    build_image
                    deploy_services "prod"
                    ;;
                3)
                    show_logs
                    ;;
                4)
                    stop_services
                    ;;
                5)
                    health_check
                    ;;
                6)
                    backup_data
                    ;;
                7)
                    cleanup
                    ;;
                8)
                    info "退出"
                    exit 0
                    ;;
                *)
                    warn "无效选择"
                    ;;
            esac
            
            echo
            read -p "按回车继续..."
        done
    else
        # 命令行模式
        case $1 in
            "build")
                build_image
                ;;
            "deploy")
                build_image
                deploy_services ${2:-dev}
                ;;
            "logs")
                show_logs
                ;;
            "stop")
                stop_services
                ;;
            "health")
                health_check
                ;;
            "backup")
                backup_data
                ;;
            "clean")
                cleanup
                ;;
            *)
                echo "用法: $0 [build|deploy|logs|stop|health|backup|clean]"
                exit 1
                ;;
        esac
    fi
}

# 运行主函数
main "$@"