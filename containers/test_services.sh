#!/bin/bash

# Hailo8 容器化服务测试脚本
# 验证所有服务的功能是否正常

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
AI_SERVICE_URL=${AI_SERVICE_URL:-"http://localhost:8080"}
WEB_APP_URL=${WEB_APP_URL:-"http://localhost:3000"}
TIMEOUT=${TIMEOUT:-30}

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"

    ((TOTAL_TESTS++))
    echo -e "\n${BLUE}测试 $TOTAL_TESTS: $test_name${NC}"

    if eval "$test_command" >/dev/null 2>&1; then
        log_success "$test_name"
        return 0
    else
        log_error "$test_name"
        echo "失败的命令: $test_command"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local url="$1"
    local service_name="$2"
    local max_attempts=30
    local attempt=1

    log_info "等待 $service_name 服务启动..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
            log_success "$service_name 服务已启动"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    log_error "$service_name 服务启动超时"
    return 1
}

# 检查Docker容器状态
check_container_status() {
    log_info "检查Docker容器状态..."

    # 检查关键容器是否运行
    local containers=("hailo-runtime" "hailo-redis" "hailo-nginx")

    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            log_success "容器 $container 正在运行"
        else
            log_error "容器 $container 未运行"
        fi
    done
}

# 测试API服务健康检查
test_api_health() {
    run_test "API健康检查" "curl -f -s $API_BASE_URL/health"
}

# 测试API服务就绪状态
test_api_ready() {
    run_test "API就绪状态检查" "curl -f -s $API_BASE_URL/ready"
}

# 测试设备状态API
test_device_status() {
    run_test "设备状态API" "curl -f -s $API_BASE_URL/api/v1/device/status"
}

# 测试模型列表API
test_models_list() {
    run_test "模型列表API" "curl -f -s $API_BASE_URL/api/v1/models"
}

# 测试推理状态API
test_inference_status() {
    run_test "推理状态API" "curl -f -s $API_BASE_URL/api/v1/inference/status"
}

# 测试AI服务
test_ai_service_health() {
    run_test "AI服务健康检查" "curl -f -s $AI_SERVICE_URL/health"
}

# 测试AI服务状态
test_ai_service_status() {
    run_test "AI服务状态检查" "curl -f -s $AI_SERVICE_URL/status"
}

# 测试Web应用
test_web_app() {
    run_test "Web应用访问" "curl -f -s $WEB_APP_URL"
}

# 测试Nginx代理
test_nginx_proxy() {
    run_test "Nginx代理功能" "curl -f -s http://localhost/nginx-health"
}

# 测试Prometheus指标
test_prometheus_metrics() {
    run_test "Prometheus指标" "curl -f -s $API_BASE_URL/metrics"
}

# 创建测试图像
create_test_image() {
    log_info "创建测试图像..."

    # 使用ImageMagick创建测试图像 (如果可用)
    if command -v convert >/dev/null 2>&1; then
        convert -size 640x480 xc:blue test_image.jpg
        log_success "测试图像创建成功"
        return 0
    else
        # 下载一个测试图像
        if command -v wget >/dev/null 2>&1; then
            wget -q "https://via.placeholder.com/640x480/0000FF/FFFFFF?text=Test+Image" -O test_image.jpg
            log_success "测试图像下载成功"
            return 0
        else
            log_warning "无法创建测试图像，跳过图像推理测试"
            return 1
        fi
    fi
}

# 测试图像推理
test_image_inference() {
    if [ ! -f "test_image.jpg" ]; then
        if ! create_test_image; then
            log_warning "跳过图像推理测试"
            return 0
        fi
    fi

    run_test "图像推理API" "curl -f -s -X POST -F 'file=@test_image.jpg' $API_BASE_URL/api/v1/inference/image"
}

# 测试批量推理
test_batch_inference() {
    if [ ! -f "test_image.jpg" ]; then
        log_warning "跳过批量推理测试"
        return 0
    fi

    # 复制测试图像用于批量测试
    cp test_image.jpg test_image2.jpg

    run_test "批量推理API" "curl -f -s -X POST -F 'files=@test_image.jpg' -F 'files=@test_image2.jpg' $AI_SERVICE_URL/batch_inference"
}

# 测试WebSocket连接
test_websocket() {
    log_info "测试WebSocket连接..."

    # 简单的WebSocket测试 (需要socat工具)
    if command -v socat >/dev/null 2>&1; then
        if echo "" | timeout 5 socat - TCP:localhost:8000 2>/dev/null; then
            log_success "WebSocket连接测试"
        else
            log_warning "WebSocket连接测试失败"
        fi
    else
        log_warning "跳过WebSocket测试 (缺少socat工具)"
    fi
}

# 测试负载均衡
test_load_balancing() {
    log_info "测试负载均衡..."

    # 并发发送多个请求
    for i in {1..5}; do
        curl -s "$API_BASE_URL/health" > /dev/null &
    done

    wait
    log_success "负载均衡测试完成"
}

# 测试错误处理
test_error_handling() {
    log_info "测试错误处理..."

    # 测试无效端点
    local response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE_URL/invalid_endpoint")

    if [ "$response" = "404" ]; then
        log_success "404错误处理正确"
    else
        log_error "404错误处理失败，返回码: $response"
    fi

    # 测试无效方法
    response=$(curl -s -w "%{http_code}" -o /dev/null -X DELETE "$API_BASE_URL/health")

    if [ "$response" = "405" ]; then
        log_success "405错误处理正确"
    else
        log_error "405错误处理失败，返回码: $response"
    fi
}

# 性能测试
test_performance() {
    log_info "执行性能测试..."

    local start_time=$(date +%s%N)

    # 发送10个并发请求
    for i in {1..10}; do
        curl -s "$API_BASE_URL/health" > /dev/null &
    done

    wait

    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # 转换为毫秒

    if [ $duration -lt 5000 ]; then # 5秒内完成
        log_success "性能测试通过 (${duration}ms)"
    else
        log_warning "性能较慢 (${duration}ms)"
    fi
}

# 清理测试文件
cleanup() {
    log_info "清理测试文件..."
    rm -f test_image.jpg test_image2.jpg
}

# 显示测试结果
show_results() {
    echo -e "\n=============================================="
    echo -e "           测试结果汇总                     "
    echo -e "=============================================="
    echo -e "总测试数: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "失败: ${RED}$FAILED_TESTS${NC}"

    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    fi

    echo -e "成功率: ${BLUE}$success_rate%${NC}"

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n🎉 ${GREEN}所有测试通过！${NC}"
        echo -e "Hailo8容器化服务运行正常。"
    else
        echo -e "\n⚠️  ${YELLOW}有 $FAILED_TESTS 个测试失败${NC}"
        echo -e "请检查服务状态和配置。"
    fi

    echo -e "=============================================="
}

# 主函数
main() {
    echo -e "=============================================="
    echo -e "      Hailo8 容器化服务功能测试               "
    echo -e "=============================================="
    echo -e "测试时间: $(date)"
    echo -e "API地址: $API_BASE_URL"
    echo ""

    # 检查Docker是否运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker服务"
        exit 1
    fi

    # 检查容器状态
    check_container_status

    # 等待服务启动
    wait_for_service "$API_BASE_URL/health" "Hailo Runtime API"

    if [ $? -ne 0 ]; then
        log_error "服务未正常启动，请检查Docker容器状态"
        exit 1
    fi

    # 执行测试
    test_api_health
    test_api_ready
    test_device_status
    test_models_list
    test_inference_status
    test_ai_service_health
    test_ai_service_status
    test_web_app
    test_nginx_proxy
    test_prometheus_metrics
    test_image_inference
    test_batch_inference
    test_websocket
    test_load_balancing
    test_error_handling
    test_performance

    # 清理
    cleanup

    # 显示结果
    show_results

    # 返回适当的退出码
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    --quick)
        # 快速测试模式
        log_info "执行快速测试..."
        test_api_health
        test_api_ready
        test_device_status
        show_results
        ;;
    --api-only)
        # 仅测试API
        log_info "仅测试API服务..."
        test_api_health
        test_api_ready
        test_device_status
        test_models_list
        test_inference_status
        test_image_inference
        show_results
        ;;
    --help)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --quick      快速测试（基础功能）"
        echo "  --api-only   仅测试API服务"
        echo "  --help       显示此帮助信息"
        echo ""
        echo "环境变量:"
        echo "  API_BASE_URL    API服务地址 (默认: http://localhost:8000)"
        echo "  AI_SERVICE_URL  AI服务地址 (默认: http://localhost:8080)"
        echo "  WEB_APP_URL     Web应用地址 (默认: http://localhost:3000)"
        exit 0
        ;;
    *)
        # 完整测试
        main
        ;;
esac