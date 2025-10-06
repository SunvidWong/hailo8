#!/bin/bash
# Hailo8 + NVIDIA + Frigate 零配置一键部署脚本
# 自动检测硬件并配置Frigate，无需手动配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
COMPOSE_FILE="docker-compose.zero-config.yml"
PROJECT_NAME="hailo8-frigate-zero"

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_service() {
    echo -e "${CYAN}[SERVICE]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         Hailo8 + NVIDIA + Frigate 零配置部署器           ║"
    echo "║        自动检测硬件 · 无需手动配置 · 一键启动             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查权限
    if ! docker info &> /dev/null; then
        log_error "无法访问Docker，请检查用户权限或运行 'sudo usermod -aG docker \$USER'"
        exit 1
    fi

    # 检查硬件
    log_info "检测可用硬件..."

    # 检查Hailo8
    if lspci | grep -i hailo > /dev/null 2>&1; then
        log_success "✓ 检测到Hailo8 PCIe设备"
        HAILO_AVAILABLE=true
    else
        log_warning "⚠ 未检测到Hailo8 PCIe设备"
        HAILO_AVAILABLE=false
    fi

    # 检查NVIDIA
    if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
        log_success "✓ 检测到NVIDIA GPU"
        NVIDIA_AVAILABLE=true
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
        log_info "  GPU: $GPU_INFO"
    else
        log_warning "⚠ 未检测到NVIDIA GPU或驱动"
        NVIDIA_AVAILABLE=false
    fi

    if [ "$HAILO_AVAILABLE" = false ] && [ "$NVIDIA_AVAILABLE" = false ]; then
        log_error "未检测到任何支持的AI加速硬件"
        exit 1
    fi

    log_success "✅ 系统要求检查完成"
}

# 创建必要的目录
create_directories() {
    log_step "创建必要的目录..."

    directories=(
        "config"
        "logs"
        "models"
        "media/frigate"
        "media/recordings"
        "media/clips"
        "monitoring"
        "temp"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "  创建目录: $dir"
        fi
    done

    # 设置权限
    chmod 755 config logs models temp
    chmod 777 media

    log_success "✅ 目录结构创建完成"
}

# 生成配置文件
generate_configs() {
    log_step "生成配置文件..."

    # 生成MQTT配置
    if [ ! -f "config/mosquitto.conf" ]; then
        cat > config/mosquitto.conf << EOF
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

listener 9001
protocol websockets
EOF
        log_info "  生成MQTT配置"
    fi

    # 生成Prometheus配置
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-acceleration-service'
    static_configs:
      - targets: ['ai-acceleration-service:8000']
    metrics_path: '/metrics'

  - job_name: 'frigate'
    static_configs:
      - targets: ['frigate:5000']
    metrics_path: '/metrics'
EOF
        log_info "  生成Prometheus配置"
    fi

    log_success "✅ 配置文件生成完成"
}

# 构建镜像
build_images() {
    log_step "构建Docker镜像..."

    if [ ! -f "Dockerfile" ] && [ -d "hailo-runtime" ]; then
        cd hailo-runtime
    fi

    log_info "构建AI加速服务镜像..."
    docker build -t hailo8/nvidia-hailo:latest . --build-arg SUPPORT_NVIDIA=$NVIDIA_AVAILABLE --build-arg SUPPORT_HAILO=$HAILO_AVAILABLE

    if [ -d "../hailo-runtime" ]; then
        cd ..
    fi

    log_success "✅ 镜像构建完成"
}

# 启动服务
start_services() {
    log_step "启动AI监控服务..."

    # 创建网络
    log_info "创建Docker网络..."
    docker network create ai-monitoring-network 2>/dev/null || true

    # 启动核心服务
    log_service "启动AI加速服务..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d ai-acceleration-service redis

    # 等待AI服务启动
    log_info "等待AI加速服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "✅ AI加速服务已启动"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "AI加速服务启动超时"
            exit 1
        fi
        sleep 2
        echo -n "."
    done
    echo

    # 显示硬件检测结果
    log_info "硬件检测结果:"
    curl -s http://localhost:8000/ai/hardware | jq '.' 2>/dev/null || echo "无法获取硬件信息"

    # 启动MQTT和自动配置服务
    log_service "启动MQTT和自动配置服务..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d mqtt auto-configurator

    # 等待自动配置完成
    log_info "等待Frigate自动配置..."
    sleep 10

    # 启动Frigate
    log_service "启动Frigate NVR..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d frigate

    # 启动监控服务
    log_service "启动监控服务..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d prometheus grafana

    log_success "✅ 所有服务启动完成"
}

# 验证部署
verify_deployment() {
    log_step "验证部署状态..."

    services=(
        "ai-acceleration-service:8000"
        "frigate:5000"
        "prometheus:9090"
        "grafana:3000"
    )

    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)

        for i in {1..10}; do
            if curl -s "http://localhost:$port" > /dev/null 2>&1; then
                log_success "✅ $name 服务运行正常 (端口 $port)"
                break
            fi
            if [ $i -eq 10 ]; then
                log_warning "⚠ $name 服务可能还在启动中 (端口 $port)"
            fi
            sleep 3
        done
    done

    # 检查Frigate配置
    if [ -f "config/frigate.yml" ]; then
        log_success "✅ Frigate配置文件已生成"

        # 显示配置摘要
        detectors=$(grep -A 5 "detectors:" config/frigate.yml | grep -c "type: remote" || echo "0")
        log_info "  配置的检测器数量: $detectors"
    fi

    # 检查服务状态
    log_info "服务状态总览:"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps
}

# 显示访问信息
show_access_info() {
    log_step "显示访问信息..."

    echo ""
    echo -e "${GREEN}🎉 零配置AI监控系统部署完成！${NC}"
    echo ""
    echo -e "${CYAN}📱 访问地址:${NC}"
    echo -e "  • Frigate Web界面: ${YELLOW}http://localhost:5000${NC}"
    echo -e "  • Grafana监控面板: ${YELLOW}http://localhost:3000${NC}"
    echo -e "    用户名: admin, 密码: hailo8_frigate"
    echo -e "  • Prometheus指标: ${YELLOW}http://localhost:9090${NC}"
    echo -e "  • AI加速服务API: ${YELLOW}http://localhost:8000${NC}"
    echo ""
    echo -e "${CYAN}🔧 API端点:${NC}"
    echo -e "  • 硬件状态: ${YELLOW}curl http://localhost:8000/ai/hardware${NC}"
    echo -e "  • Frigate状态: ${YELLOW}curl http://localhost:8000/frigate/status${NC}"
    echo -e "  • 推理测试: ${YELLOW}curl -X POST -H 'Content-Type: application/json' -d '{\"image\":[[[255,0,0]]],\"engine\":\"auto\"}' http://localhost:8000/ai/infer${NC}"
    echo ""
    echo -e "${CYAN}📊 监控指标:${NC}"
    echo -e "  • AI推理性能: 实时延迟和吞吐量"
    echo -e "  • 硬件利用率: GPU内存、Hailo8使用率"
    echo -e "  • Frigate检测: 目标检测统计和准确率"
    echo ""
    echo -e "${CYAN}🛠️ 管理命令:${NC}"
    echo -e "  • 查看日志: ${YELLOW}docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f${NC}"
    echo -e "  • 重启服务: ${YELLOW}docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart${NC}"
    echo -e "  • 停止服务: ${YELLOW}docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down${NC}"
    echo ""
    echo -e "${GREEN}✨ 现在您可以访问Frigate Web界面开始配置摄像头了！${NC}"
    echo ""
}

# 主函数
main() {
    show_banner

    log_info "开始零配置AI监控系统部署..."

    # 检查是否在正确的目录
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "未找到 $COMPOSE_FILE 文件，请确保在正确的目录中运行此脚本"
        exit 1
    fi

    check_requirements
    create_directories
    generate_configs
    build_images
    start_services
    verify_deployment
    show_access_info

    log_success "🚀 零配置部署完成！"
}

# 处理中断信号
trap 'log_warning "部署被中断"; exit 1' INT TERM

# 运行主函数
main "$@"