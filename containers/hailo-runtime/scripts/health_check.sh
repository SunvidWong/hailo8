#!/bin/bash

# Health Check Script for Hailo8 Runtime Container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_HOST=${HAILO_API_HOST:-"localhost"}
API_PORT=${HAILO_API_PORT:-8000}
GRPC_PORT=${HAILO_GRPC_PORT:-50051}

# Health check endpoints
API_HEALTH_URL="http://${API_HOST}:${API_PORT}/health"
API_READY_URL="http://${API_HOST}:${API_PORT}/ready"

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required processes are running
check_processes() {
    log_info "检查服务进程..."

    # Check if main API process is running
    if pgrep -f "api/main.py" > /dev/null; then
        log_info "✓ API服务进程运行正常"
    else
        log_error "✗ API服务进程未运行"
        return 1
    fi
}

# Check device accessibility
check_hailo_device() {
    log_info "检查Hailo设备访问..."

    # Check if device nodes exist
    if [[ -e "/dev/hailo0" ]] || [[ -e "/dev/hailo1" ]]; then
        log_info "✓ Hailo设备节点存在"

        # Try to access device (this may not work if no hardware is present)
        if ls /dev/hailo* 2>/dev/null; then
            log_info "✓ 设备节点可访问"
        else
            log_warning "⚠ 设备节点存在但无法访问"
        fi
    else
        log_warning "⚠ 未找到Hailo设备节点 (正常情况，如果没有连接硬件)"
    fi
}

# Check kernel module
check_kernel_module() {
    log_info "检查内核模块..."

    if lsmod | grep -q hailo1x_pci; then
        log_info "✓ Hailo内核模块已加载"

        # Get module info
        local module_info=$(modinfo hailo1x_pci 2>/dev/null | head -3)
        echo "模块信息:"
        echo "$module_info"
    else
        log_warning "⚠ Hailo内核模块未加载"
    fi
}

# Check API health endpoint
check_api_health() {
    log_info "检查API健康状态..."

    # Wait a moment for the service to be ready
    sleep 2

    # Check health endpoint
    if curl -s --connect-timeout 5 "$API_HEALTH_URL" > /dev/null; then
        log_info "✓ API健康检查通过"

        # Check readiness endpoint
        if curl -s --connect-timeout 5 "$API_READY_URL" > /dev/null; then
            log_info "✓ API就绪状态正常"
        else
            log_warning "⚠ API尚未完全就绪"
        fi
    else
        log_error "✗ API健康检查失败"
        return 1
    fi
}

# Check network ports
check_network_ports() {
    log_info "检查网络端口..."

    # Check HTTP API port
    if netstat -ln | grep -q ":$API_PORT "; then
        log_info "✓ HTTP API端口 $API_PORT 正在监听"
    else
        log_error "✗ HTTP API端口 $API_PORT 未监听"
        return 1
    fi

    # Check gRPC port
    if netstat -ln | grep -q ":$GRPC_PORT "; then
        log_info "✓ gRPC端口 $GRPC_PORT 正在监听"
    else
        log_warning "⚠ gRPC端口 $GRPC_PORT 未监听"
    fi
}

# Check system resources
check_system_resources() {
    log_info "检查系统资源..."

    # Check memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    log_info "内存使用率: $mem_usage"

    # Check disk space
    local disk_usage=$(df /app | awk 'NR==2{print $5}')
    log_info "磁盘使用率: $disk_usage"

    # Check CPU load
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    log_info "CPU负载: $load_avg"

    # Memory usage warning
    if [[ $(free | awk 'NR==2{printf "%.0f", $3*100/$2}') -gt 80 ]]; then
        log_warning "⚠ 内存使用率过高"
    fi

    # Disk space warning
    if [[ ${disk_usage%?} -gt 85 ]]; then
        log_warning "⚠ 磁盘空间不足"
    fi
}

# Check log files for errors
check_log_errors() {
    log_info "检查日志错误..."

    local log_dir="/app/logs"
    if [[ -d "$log_dir" ]]; then
        local error_count=$(find "$log_dir" -name "*.log" -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | wc -l)
        if [[ $error_count -gt 0 ]]; then
            log_warning "⚠ 发现 $error_count 个日志文件包含错误信息"
        else
            log_info "✓ 未发现日志错误"
        fi
    else
        log_info "日志目录不存在，跳过日志检查"
    fi
}

# Main health check function
main() {
    echo "=============================================="
    echo "      Hailo8 Runtime Container 健康检查      "
    echo "=============================================="
    echo "检查时间: $(date)"
    echo "容器ID: $(hostname)"
    echo ""

    local exit_code=0

    # Run all checks
    check_processes || exit_code=1
    check_hailo_device
    check_kernel_module
    check_api_health || exit_code=1
    check_network_ports || exit_code=1
    check_system_resources
    check_log_errors

    echo ""
    echo "=============================================="

    if [[ $exit_code -eq 0 ]]; then
        log_info "✓ 所有健康检查通过"
        echo "状态: 健康"
    else
        log_error "✗ 健康检查失败"
        echo "状态: 不健康"
    fi

    echo "=============================================="

    exit $exit_code
}

# Run health check if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi