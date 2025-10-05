#!/bin/bash

# Hailo8 远程部署脚本
# 支持自动化远程服务器部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 默认配置
DEFAULT_SSH_PORT=22
DEFAULT_DEPLOY_USER=root
DEFAULT_DEPLOY_PATH=/opt/hailo8
DEFAULT_COMPOSE_FILE=docker-compose.remote.yml

# 帮助信息
show_help() {
    cat << EOF
🚀 Hailo8 远程部署脚本

用法: $0 [选项] <服务器地址>

选项:
  -p, --port PORT        SSH端口 (默认: 22)
  -u, --user USER        SSH用户 (默认: root)
  -d, --path PATH        部署路径 (默认: /opt/hailo8)
  -f, --file FILE        Compose文件 (默认: docker-compose.remote.yml)
  -e, --env ENV          环境文件 (默认: .env.remote)
  -b, --backup           部署前备份现有服务
  -r, --rollback         回滚到上一个版本
  -s, --skip-ssl         跳过SSL证书检查
  -h, --help             显示此帮助信息

示例:
  # 基本部署
  $0 192.168.1.100

  # 指定用户和端口
  $0 -u deploy -p 2222 192.168.1.100

  # 带备份的部署
  $0 -b 192.168.1.100

  # 回滚部署
  $0 -r 192.168.1.100

  # 自定义部署路径
  $0 -d /custom/path 192.168.1.100

环境变量:
  SSH_PRIVATE_KEY        SSH私钥文件路径
  DEPLOY_KEY             部署密钥内容
  SKIP_HEALTH_CHECK      跳过健康检查
  TIMEOUT                连接超时时间 (默认: 300秒)

EOF
}

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

log_command() {
    echo -e "${CYAN}[COMMAND]${NC} $1"
}

# 解析命令行参数
parse_args() {
    SSH_PORT=$DEFAULT_SSH_PORT
    DEPLOY_USER=$DEFAULT_DEPLOY_USER
    DEPLOY_PATH=$DEFAULT_DEPLOY_PATH
    COMPOSE_FILE=$DEFAULT_COMPOSE_FILE
    ENV_FILE=.env.remote
    BACKUP=false
    ROLLBACK=false
    SKIP_SSL=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                SSH_PORT="$2"
                shift 2
                ;;
            -u|--user)
                DEPLOY_USER="$2"
                shift 2
                ;;
            -d|--path)
                DEPLOY_PATH="$2"
                shift 2
                ;;
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -b|--backup)
                BACKUP=true
                shift
                ;;
            -r|--rollback)
                ROLLBACK=true
                shift
                ;;
            -s|--skip-ssl)
                SKIP_SSL=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                SERVER_ADDRESS="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$SERVER_ADDRESS" ]]; then
        log_error "请提供服务器地址"
        show_help
        exit 1
    fi
}

# 验证前置条件
validate_prerequisites() {
    log_step "验证前置条件..."

    # 检查SSH连接
    log_info "测试SSH连接: $DEPLOY_USER@$SERVER_ADDRESS:$SSH_PORT"
    if ! ssh -p $SSH_PORT -o ConnectTimeout=10 -o BatchMode=yes "$DEPLOY_USER@$SERVER_ADDRESS" "echo 'SSH连接成功'" 2>/dev/null; then
        log_error "SSH连接失败，请检查："
        log_error "1. 服务器地址是否正确: $SERVER_ADDRESS"
        log_error "2. SSH端口是否开放: $SSH_PORT"
        log_error "3. SSH密钥是否配置正确"
        log_error "4. 用户权限是否足够"
        exit 1
    fi

    # 检查Docker是否安装
    log_info "检查Docker安装状态..."
    if ! ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" "command -v docker" 2>/dev/null; then
        log_error "远程服务器未安装Docker"
        log_info "尝试自动安装Docker..."
        install_docker
    fi

    # 检查Docker Compose
    log_info "检查Docker Compose安装状态..."
    if ! ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" "command -v docker-compose" 2>/dev/null; then
        log_error "远程服务器未安装Docker Compose"
        log_info "尝试自动安装Docker Compose..."
        install_docker_compose
    fi

    # 检查磁盘空间
    log_info "检查磁盘空间..."
    local disk_usage=$(ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" "df -h $DEPLOY_PATH 2>/dev/null | tail -1 | awk '{print \$5}' | sed 's/%//'")
    if [[ $disk_usage -gt 80 ]]; then
        log_warning "磁盘空间使用率较高: ${disk_usage}%"
    fi

    log_success "前置条件验证完成"
}

# 安装Docker
install_docker() {
    log_info "在远程服务器安装Docker..."

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << 'EOF'
set -e

# 检测系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION_ID=$VERSION_ID
else
    echo "无法检测系统类型"
    exit 1
fi

# 安装Docker
case $OS in
    ubuntu|debian)
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io
        ;;
    centos|rhel|fedora)
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
        ;;
    *)
        echo "不支持的系统类型: $OS"
        exit 1
        ;;
esac

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 添加用户到docker组
usermod -aG docker $USER

echo "Docker安装完成"
EOF

    if [[ $? -eq 0 ]]; then
        log_success "Docker安装成功"
    else
        log_error "Docker安装失败"
        exit 1
    fi
}

# 安装Docker Compose
install_docker_compose() {
    log_info "在远程服务器安装Docker Compose..."

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << 'EOF'
set -e

# 下载Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 创建软链接
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 验证安装
docker-compose --version

echo "Docker Compose安装完成"
EOF

    if [[ $? -eq 0 ]]; then
        log_success "Docker Compose安装成功"
    else
        log_error "Docker Compose安装失败"
        exit 1
    fi
}

# 备份现有服务
backup_service() {
    if [[ "$BACKUP" != true ]]; then
        return 0
    fi

    log_step "备份现有服务..."

    local backup_name="hailo8-backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$DEPLOY_PATH/../backups/$backup_name"

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << EOF
set -e

# 创建备份目录
mkdir -p "$backup_path"

# 停止现有服务
if [ -f "$DEPLOY_PATH/docker-compose.yml" ]; then
    cd "$DEPLOY_PATH"
    docker-compose down || true
fi

# 备份数据目录
if [ -d "$DEPLOY_PATH/data" ]; then
    cp -r "$DEPLOY_PATH/data" "$backup_path/"
fi

# 备份配置文件
if [ -f "$DEPLOY_PATH/.env" ]; then
    cp "$DEPLOY_PATH/.env" "$backup_path/"
fi

# 备份Docker Compose文件
if [ -f "$DEPLOY_PATH/docker-compose.yml" ]; then
    cp "$DEPLOY_PATH/docker-compose.yml" "$backup_path/"
fi

# 压缩备份
cd "$(dirname "$backup_path")"
tar -czf "$backup_name.tar.gz" "$backup_name"
rm -rf "$backup_path"

echo "备份完成: $backup_name.tar.gz"
EOF

    if [[ $? -eq 0 ]]; then
        log_success "服务备份完成: $backup_name.tar.gz"
    else
        log_warning "服务备份失败，继续部署..."
    fi
}

# 创建部署目录结构
create_directories() {
    log_step "创建部署目录结构..."

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << EOF
set -e

# 创建主目录
mkdir -p "$DEPLOY_PATH"
mkdir -p "$DEPLOY_PATH/config"
mkdir -p "$DEPLOY_PATH/nginx/ssl"
mkdir -p "$DEPLOY_PATH/monitoring"
mkdir -p "$DEPLOY_PATH/logging"
mkdir -p "$DEPLOY_PATH/backups"
mkdir -p "$DEPLOY_PATH/data/models"
mkdir -p "$DEPLOY_PATH/data/logs"
mkdir -p "$DEPLOY_PATH/data/temp"

# 设置权限
chown -R $DEPLOY_USER:$DEPLOY_USER "$DEPLOY_PATH"
chmod 755 "$DEPLOY_PATH"

echo "目录结构创建完成"
EOF

    log_success "部署目录结构创建完成"
}

# 上传文件到远程服务器
upload_files() {
    log_step "上传部署文件..."

    # 上传Docker Compose文件
    log_info "上传Docker Compose配置..."
    scp -P $SSH_PORT "$COMPOSE_FILE" "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/docker-compose.yml"

    # 上传环境变量文件
    if [[ -f "$ENV_FILE" ]]; then
        log_info "上传环境变量配置..."
        scp -P $SSH_PORT "$ENV_FILE" "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/.env"
    fi

    # 上传配置文件
    log_info "上传配置文件..."
    scp -P $SSH_PORT -r config/* "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/config/" 2>/dev/null || true
    scp -P $SSH_PORT -r nginx/* "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/nginx/" 2>/dev/null || true
    scp -P $SSH_PORT -r monitoring/* "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/monitoring/" 2>/dev/null || true
    scp -P $SSH_PORT -r logging/* "$DEPLOY_USER@$SERVER_ADDRESS:$DEPLOY_PATH/logging/" 2>/dev/null || true

    log_success "文件上传完成"
}

# 部署服务
deploy_service() {
    log_step "部署Hailo8服务..."

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << EOF
set -e

cd "$DEPLOY_PATH"

# 拉取最新镜像
echo "拉取Docker镜像..."
docker-compose pull

# 构建自定义镜像
echo "构建自定义镜像..."
docker-compose build --no-cache

# 停止现有服务
echo "停止现有服务..."
docker-compose down || true

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo "服务部署完成"
EOF

    if [[ $? -eq 0 ]]; then
        log_success "服务部署成功"
    else
        log_error "服务部署失败"
        exit 1
    fi
}

# 健康检查
health_check() {
    log_step "执行健康检查..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "健康检查尝试 $attempt/$max_attempts..."

        # 检查API服务
        if curl -s --connect-timeout 5 "http://$SERVER_ADDRESS:8000/health" >/dev/null 2>&1; then
            log_success "API服务健康检查通过"
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            log_error "健康检查失败，服务可能未正常启动"
            log_info "请检查服务日志: ssh -p $SSH_PORT $DEPLOY_USER@$SERVER_ADDRESS 'cd $DEPLOY_PATH && docker-compose logs'"
            return 1
        fi

        sleep 10
        ((attempt++))
    done

    # 检查其他服务
    log_info "检查其他服务状态..."
    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << EOF
cd "$DEPLOY_PATH"

echo "=== 容器状态 ==="
docker-compose ps

echo "=== 服务端口状态 ==="
netstat -tlnp | grep -E ':(8000|8080|3001|5601|6379|9200)' || echo "部分端口未监听"

echo "=== 磁盘使用情况 ==="
df -h "$DEPLOY_PATH"

echo "=== 内存使用情况 ==="
free -h
EOF

    log_success "健康检查完成"
}

# 回滚服务
rollback_service() {
    log_step "回滚服务..."

    ssh -p $SSH_PORT "$DEPLOY_USER@$SERVER_ADDRESS" << EOF
set -e

# 查找最新备份
BACKUP_FILE=\$(ls -t "$DEPLOY_PATH/../backups/hailo8-backup-"*.tar.gz 2>/dev/null | head -1)

if [ -z "\$BACKUP_FILE" ]; then
    echo "未找到备份文件"
    exit 1
fi

echo "使用备份文件: \$BACKUP_FILE"

# 停止当前服务
cd "$DEPLOY_PATH"
docker-compose down || true

# 解压备份
cd "\$(dirname "\$BACKUP_FILE")"
tar -xzf "\$(basename "\$BACKUP_FILE")"

# 恢复数据
BACKUP_DIR=\$(basename "\$BACKUP_FILE" .tar.gz)
if [ -d "\$BACKUP_DIR/data" ]; then
    rm -rf "$DEPLOY_PATH/data"
    cp -r "\$BACKUP_DIR/data" "$DEPLOY_PATH/"
fi

# 恢复配置文件
if [ -f "\$BACKUP_DIR/.env" ]; then
    cp "\$BACKUP_DIR/.env" "$DEPLOY_PATH/"
fi

# 恢复Docker Compose文件
if [ -f "\$BACKUP_DIR/docker-compose.yml" ]; then
    cp "\$BACKUP_DIR/docker-compose.yml" "$DEPLOY_PATH/"
fi

# 清理临时文件
rm -rf "\$BACKUP_DIR"

# 重启服务
cd "$DEPLOY_PATH"
docker-compose up -d

echo "回滚完成"
EOF

    if [[ $? -eq 0 ]]; then
        log_success "服务回滚成功"
    else
        log_error "服务回滚失败"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"
    echo ""
    echo "🎉 Hailo8服务部署成功！"
    echo ""
    echo "📍 服务地址:"
    echo "   API服务:     http://$SERVER_ADDRESS:8000"
    echo "   Web界面:     http://$SERVER_ADDRESS:3000"
    echo "   Grafana:     http://$SERVER_ADDRESS:3001"
    echo "   Kibana:      http://$SERVER_ADDRESS:5601"
    echo ""
    echo "🔑 访问信息:"
    echo "   Grafana:     admin / \${GRAFANA_PASSWORD:-admin123}"
    echo "   部署路径:     $DEPLOY_PATH"
    echo ""
    echo "🔧 管理命令:"
    echo "   查看状态:     ssh -p $SSH_PORT $DEPLOY_USER@$SERVER_ADDRESS 'cd $DEPLOY_PATH && docker-compose ps'"
    echo "   查看日志:     ssh -p $SSH_PORT $DEPLOY_USER@$SERVER_ADDRESS 'cd $DEPLOY_PATH && docker-compose logs -f'"
    echo "   重启服务:     ssh -p $SSH_PORT $DEPLOY_USER@$SERVER_ADDRESS 'cd $DEPLOY_PATH && docker-compose restart'"
    echo "   停止服务:     ssh -p $SSH_PORT $DEPLOY_USER@$SERVER_ADDRESS 'cd $DEPLOY_PATH && docker-compose down'"
    echo ""
    echo "📊 监控面板:"
    echo "   系统监控:     http://$SERVER_ADDRESS:3001"
    echo "   日志分析:     http://$SERVER_ADDRESS:5601"
    echo "   API指标:      http://$SERVER_ADDRESS:9091"
    echo ""
}

# 主函数
main() {
    echo "🚀 Hailo8 远程部署脚本"
    echo "================================"

    # 解析参数
    parse_args "$@"

    # 显示部署信息
    log_info "部署配置:"
    log_info "  服务器地址: $SERVER_ADDRESS:$SSH_PORT"
    log_info "  部署用户: $DEPLOY_USER"
    log_info "  部署路径: $DEPLOY_PATH"
    log_info "  Compose文件: $COMPOSE_FILE"
    log_info "  环境文件: $ENV_FILE"
    echo ""

    # 执行部署流程
    if [[ "$ROLLBACK" == true ]]; then
        validate_prerequisites
        rollback_service
        show_deployment_info
    else
        validate_prerequisites
        backup_service
        create_directories
        upload_files
        deploy_service
        health_check
        show_deployment_info
    fi

    log_success "部署任务完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"