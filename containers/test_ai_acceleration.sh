#!/bin/bash
# AI加速服务测试脚本
# 测试Hailo8 + NVIDIA双硬件加速功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务配置
SERVICE_URL="http://localhost:8000"
TIMEOUT=30

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

# 测试函数
test_service_health() {
    log_info "测试服务健康状态..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/health" > /dev/null; then
        log_success "✓ 服务健康检查通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 服务健康检查失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_hardware_detection() {
    log_info "测试硬件检测功能..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")

    if echo "$response" | jq -e '.available_engines | length > 0' > /dev/null 2>&1; then
        log_success "✓ 硬件检测成功"

        # 显示检测到的硬件
        hailo_count=$(echo "$response" | jq -r '.hailo_devices | length // 0')
        nvidia_count=$(echo "$response" | jq -r '.nvidia_devices | length // 0')

        log_info "  - Hailo8设备: $hailo_count 个"
        log_info "  - NVIDIA设备: $nvidia_count 个"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 硬件检测失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_engine_info() {
    log_info "测试推理引擎信息..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/engines")

    if echo "$response" | jq -e '.available_engines' > /dev/null 2>&1; then
        log_success "✓ 推理引擎信息获取成功"

        # 显示可用引擎
        echo "$response" | jq -r '.available_engines[]? | "  - \(.name): \(.description)"' 2>/dev/null || true

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 推理引擎信息获取失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_inference_auto() {
    log_info "测试自动推理引擎选择..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 创建测试图像数据 (3x3 RGB)
    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": $image_data,
            \"engine\": \"auto\",
            \"threshold\": 0.4
        }" \
        "$SERVICE_URL/ai/infer")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ 自动推理成功"

        engine_used=$(echo "$response" | jq -r '.engine_used // "unknown"')
        inference_time=$(echo "$response" | jq -r '.inference_time // 0')
        detections_count=$(echo "$response" | jq -r '.detections | length // 0')

        log_info "  - 使用引擎: $engine_used"
        log_info "  - 推理时间: ${inference_time}s"
        log_info "  - 检测对象: $detections_count 个"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 自动推理失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_inference_hailo() {
    log_info "测试Hailo8推理..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查Hailo8是否可用
    hardware_response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")
    hailo_available=$(echo "$hardware_response" | jq -r '.available_engines[]? | select(. == "hailo")' | wc -l)

    if [ "$hailo_available" -eq 0 ]; then
        log_warning "⚠ Hailo8不可用，跳过测试"
        TOTAL_TESTS=$((TOTAL_TESTS - 1))
        return 0
    fi

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": $image_data,
            \"engine\": \"hailo\",
            \"threshold\": 0.4
        }" \
        "$SERVICE_URL/ai/infer")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ Hailo8推理成功"

        engine_used=$(echo "$response" | jq -r '.engine_used // "unknown"')
        log_info "  - 使用引擎: $engine_used"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ Hailo8推理失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_inference_nvidia() {
    log_info "测试NVIDIA推理..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查NVIDIA是否可用
    hardware_response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")
    nvidia_available=$(echo "$hardware_response" | jq -r '.available_engines[]? | select(. == "nvidia")' | wc -l)

    if [ "$nvidia_available" -eq 0 ]; then
        log_warning "⚠ NVIDIA不可用，跳过测试"
        TOTAL_TESTS=$((TOTAL_TESTS - 1))
        return 0
    fi

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": $image_data,
            \"engine\": \"nvidia\",
            \"threshold\": 0.4
        }" \
        "$SERVICE_URL/ai/infer")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ NVIDIA推理成功"

        engine_used=$(echo "$response" | jq -r '.engines_used[0] // "unknown"')
        gpu_memory=$(echo "$response" | jq -r '.hardware_info.gpu_memory // "N/A"')

        log_info "  - 使用引擎: $engine_used"
        log_info "  - GPU内存使用: ${gpu_memory}MB"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ NVIDIA推理失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_parallel_inference() {
    log_info "测试并行推理..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查双引擎支持
    hardware_response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")
    dual_support=$(echo "$hardware_response" | jq -r '.dual_engine_support // false')

    if [ "$dual_support" != "true" ]; then
        log_warning "⚠ 双引擎不可用，跳过并行测试"
        TOTAL_TESTS=$((TOTAL_TESTS - 1))
        return 0
    fi

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": $image_data,
            \"engine\": \"parallel\",
            \"priority\": \"performance\",
            \"timeout\": 15.0
        }" \
        "$SERVICE_URL/ai/infer")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ 并行推理成功"

        engines_used=$(echo "$response" | jq -r '.engines_used | length // 0')
        parallel_execution=$(echo "$response" | jq -r '.engine_results.parallel // false')
        detections_count=$(echo "$response" | jq -r '.detections | length // 0')

        log_info "  - 使用引擎数: $engines_used"
        log_info "  - 并行执行: $parallel_execution"
        log_info "  - 检测对象: $detections_count 个"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 并行推理失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_dual_engine_fusion() {
    log_info "测试双引擎融合..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查双引擎支持
    hardware_response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")
    dual_support=$(echo "$hardware_response" | jq -r '.dual_engine_support // false')

    if [ "$dual_support" != "true" ]; then
        log_warning "⚠ 双引擎不可用，跳过融合测试"
        TOTAL_TESTS=$((TOTAL_TESTS - 1))
        return 0
    fi

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": $image_data,
            \"engine\": \"both\",
            \"priority\": \"accuracy\",
            \"threshold\": 0.3
        }" \
        "$SERVICE_URL/ai/infer")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ 双引擎融合成功"

        engines_used=$(echo "$response" | jq -r '.engines_used | length // 0')
        fusion_enabled=$(echo "$response" | jq -r '.model_info.fusion_enabled // false')
        detections_count=$(echo "$response" | jq -r '.detections | length // 0')

        log_info "  - 使用引擎数: $engines_used"
        log_info "  - 融合模式: $fusion_enabled"
        log_info "  - 检测对象: $detections_count 个"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 双引擎融合失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_load_balancing() {
    log_info "测试负载均衡..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查双引擎支持
    hardware_response=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/ai/hardware")
    dual_support=$(echo "$hardware_response" | jq -r '.dual_engine_support // false')

    if [ "$dual_support" != "true" ]; then
        log_warning "⚠ 双引擎不可用，跳过负载均衡测试"
        TOTAL_TESTS=$((TOTAL_TESTS - 1))
        return 0
    fi

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    # 执行多次负载均衡测试
    hailo_count=0
    nvidia_count=0
    successful_runs=0

    for i in {1..5}; do
        response=$(curl -s --max-time $TIMEOUT \
            -X POST \
            -H "Content-Type: application/json" \
            -d "{
                \"image\": $image_data,
                \"engine\": \"load_balance\",
                \"priority\": \"performance\"
            }" \
            "$SERVICE_URL/ai/infer")

        if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
            engine=$(echo "$response" | jq -r '.engines_used[0] // "unknown"')
            if [ "$engine" = "hailo" ]; then
                hailo_count=$((hailo_count + 1))
            elif [ "$engine" = "nvidia" ]; then
                nvidia_count=$((nvidia_count + 1))
            fi
            successful_runs=$((successful_runs + 1))
        fi
    done

    if [ "$successful_runs" -ge 3 ]; then
        log_success "✓ 负载均衡测试成功"
        log_info "  - 成功运行: $successful_runs/5 次"
        log_info "  - Hailo8选择: $hailo_count 次"
        log_info "  - NVIDIA选择: $nvidia_count 次"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 负载均衡测试失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_hardware_validation() {
    log_info "测试硬件验证..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        "$SERVICE_URL/ai/validate")

    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        log_success "✓ 硬件验证成功"

        total_engines=$(echo "$response" | jq -r '.results.total_engines // 0')
        message=$(echo "$response" | jq -r '.message // ""')

        log_info "  - $message"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 硬件验证失败"
        echo "响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

test_performance() {
    log_info "测试性能基准..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    image_data='[[[255,0,0], [255,255,255], [255,0,0]], [[0,255,0], [0,0,255], [255,255,0]], [[255,0,255], [0,255,255], [255,255,255]]]'

    # 执行多次推理测试
    total_time=0
    successful_runs=0

    for i in {1..5}; do
        start_time=$(date +%s.%N)

        response=$(curl -s --max-time $TIMEOUT \
            -X POST \
            -H "Content-Type: application/json" \
            -d "{
                \"image\": $image_data,
                \"engine\": \"auto\",
                \"threshold\": 0.4
            }" \
            "$SERVICE_URL/ai/infer")

        if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
            end_time=$(date +%s.%N)
            run_time=$(echo "$end_time - $start_time" | bc)
            total_time=$(echo "$total_time + $run_time" | bc)
            successful_runs=$((successful_runs + 1))
        fi
    done

    if [ "$successful_runs" -gt 0 ]; then
        avg_time=$(echo "scale=3; $total_time / $successful_runs" | bc)
        log_success "✓ 性能测试完成"
        log_info "  - 成功运行: $successful_runs/5 次"
        log_info "  - 平均响应时间: ${avg_time}s"

        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 性能测试失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 错误处理测试
test_error_handling() {
    log_info "测试错误处理..."

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 测试无效图像数据
    response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": \"invalid_data\",
            \"engine\": \"auto\"
        }" \
        "$SERVICE_URL/ai/infer")

    # 检查是否返回了错误状态码（4xx或5xx）
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{
            \"image\": \"invalid_data\",
            \"engine\": \"auto\"
        }" \
        "$SERVICE_URL/ai/infer")

    if [ "$http_code" -ge 400 ] && [ "$http_code" -lt 600 ]; then
        log_success "✓ 错误处理正常 (HTTP $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "✗ 错误处理异常 (HTTP $http_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 检查依赖
check_dependencies() {
    log_info "检查测试依赖..."

    # 检查curl
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi

    # 检查jq
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安装，请先安装 jq"
        exit 1
    fi

    # 检查bc
    if ! command -v bc &> /dev/null; then
        log_error "bc 未安装，请先安装 bc"
        exit 1
    fi

    log_success "✓ 所有依赖检查通过"
}

# 等待服务启动
wait_for_service() {
    log_info "等待服务启动..."

    for i in {1..30}; do
        if curl -s --max-time 5 "$SERVICE_URL/health" > /dev/null 2>&1; then
            log_success "✓ 服务已启动"
            return 0
        fi

        log_info "  等待服务启动... ($i/30)"
        sleep 2
    done

    log_error "服务启动超时"
    exit 1
}

# 显示测试结果
show_results() {
    echo ""
    echo "================================"
    echo "         测试结果汇总"
    echo "================================"
    echo -e "总测试数: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "通过测试: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "失败测试: ${RED}$FAILED_TESTS${NC}"

    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        log_success "🎉 所有测试通过！AI加速服务运行正常。"
        exit 0
    else
        echo ""
        log_error "❌ 有 $FAILED_TESTS 个测试失败，请检查服务状态。"
        exit 1
    fi
}

# 主函数
main() {
    echo "================================"
    echo "    AI加速服务测试脚本"
    echo "    Hailo8 + NVIDIA 双硬件"
    echo "================================"
    echo ""

    # 检查依赖
    check_dependencies

    # 等待服务启动
    wait_for_service

    echo ""
    log_info "开始执行测试..."
    echo ""

    # 执行测试
    test_service_health
    test_hardware_detection
    test_engine_info
    test_inference_auto
    test_inference_hailo
    test_inference_nvidia
    test_parallel_inference
    test_dual_engine_fusion
    test_load_balancing
    test_hardware_validation
    test_performance
    test_error_handling

    # 显示结果
    show_results
}

# 处理中断信号
trap 'log_warning "测试被中断"; exit 1' INT TERM

# 运行主函数
main "$@"