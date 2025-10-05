#!/bin/bash

# 使用Docker在macOS上编译Hailo8 Linux驱动的脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker Desktop for Mac"
        log_info "下载地址: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请启动Docker Desktop"
        exit 1
    fi
    
    log_success "Docker检查通过"
}

# 创建Dockerfile
create_dockerfile() {
    log_info "创建编译环境Dockerfile..."
    
    cat > Dockerfile << 'EOF'
FROM ubuntu:22.04

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 安装编译依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    linux-headers-generic \
    make \
    gcc \
    dkms \
    kmod \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /workspace

# 设置入口点
ENTRYPOINT ["/bin/bash"]
EOF
    
    log_success "Dockerfile创建完成"
}

# 构建Docker镜像
build_docker_image() {
    log_info "构建Docker编译镜像..."
    
    if docker build -t hailo8-compiler . ; then
        log_success "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 在Docker容器中编译
compile_in_docker() {
    log_info "在Docker容器中编译Hailo8驱动..."
    
    # 创建编译脚本
    cat > docker_compile_script.sh << 'EOF'
#!/bin/bash
set -e

echo "=== 开始在Docker容器中编译Hailo8驱动 ==="

# 检查源码目录
if [[ ! -d "hailort-drivers-master/linux/pcie" ]]; then
    echo "错误: 未找到驱动源码目录"
    exit 1
fi

cd hailort-drivers-master/linux/pcie

# 显示系统信息
echo "=== 系统信息 ==="
uname -a
echo "内核版本: $(uname -r)"

# 检查内核头文件
echo "=== 检查内核头文件 ==="
if [[ -d "/lib/modules/$(uname -r)/build" ]]; then
    echo "内核头文件路径: /lib/modules/$(uname -r)/build"
    ls -la /lib/modules/$(uname -r)/build/
else
    echo "警告: 标准内核头文件路径不存在，尝试使用通用头文件"
fi

# 清理之前的编译结果
echo "=== 清理编译环境 ==="
make clean 2>/dev/null || true

# 编译驱动
echo "=== 开始编译 ==="
if make all; then
    echo "=== 编译成功 ==="
    ls -la *.ko 2>/dev/null || echo "未找到.ko文件"
    
    # 显示编译结果
    if [[ -f "hailo1x_pci.ko" ]]; then
        echo "驱动模块信息:"
        file hailo1x_pci.ko
        ls -lh hailo1x_pci.ko
    fi
else
    echo "=== 编译失败 ==="
    exit 1
fi

echo "=== Docker容器编译完成 ==="
EOF

    chmod +x docker_compile_script.sh
    
    # 运行Docker容器进行编译
    if docker run --rm -v "$(pwd)":/workspace hailo8-compiler ./docker_compile_script.sh; then
        log_success "Docker容器编译完成"
    else
        log_error "Docker容器编译失败"
        exit 1
    fi
}

# 检查编译结果
check_results() {
    log_info "检查编译结果..."
    
    if [[ -f "hailort-drivers-master/linux/pcie/hailo1x_pci.ko" ]]; then
        log_success "驱动编译成功！"
        echo "驱动文件位置: $(pwd)/hailort-drivers-master/linux/pcie/hailo1x_pci.ko"
        ls -lh hailort-drivers-master/linux/pcie/hailo1x_pci.ko
        
        log_info "文件信息:"
        file hailort-drivers-master/linux/pcie/hailo1x_pci.ko
    else
        log_error "未找到编译生成的驱动文件"
        exit 1
    fi
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    rm -f Dockerfile docker_compile_script.sh
    log_success "清理完成"
}

# 显示使用说明
show_usage() {
    log_info "编译完成后的使用说明:"
    echo ""
    echo "1. 将编译好的驱动文件复制到目标Linux系统:"
    echo "   scp hailort-drivers-master/linux/pcie/hailo1x_pci.ko user@target-system:/tmp/"
    echo ""
    echo "2. 在目标系统上安装驱动:"
    echo "   sudo cp /tmp/hailo1x_pci.ko /lib/modules/\$(uname -r)/kernel/drivers/misc/"
    echo "   sudo depmod -a"
    echo "   sudo modprobe hailo1x_pci"
    echo ""
    echo "3. 验证驱动加载:"
    echo "   lsmod | grep hailo"
    echo "   ls -la /dev/hailo*"
    echo ""
    echo "注意: 编译的驱动需要在相同或兼容的内核版本上使用"
}

# 主函数
main() {
    log_info "开始使用Docker编译Hailo8驱动"
    
    # 解析命令行参数
    CLEANUP=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cleanup)
                CLEANUP=false
                shift
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --no-cleanup   保留临时文件"
                echo "  --help         显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 检查源码是否存在
    if [[ ! -d "hailort-drivers-master" ]]; then
        log_error "未找到驱动源码目录，请确保已下载并解压源码"
        exit 1
    fi
    
    # 执行编译流程
    check_docker
    create_dockerfile
    build_docker_image
    compile_in_docker
    check_results
    
    if [[ "$CLEANUP" == true ]]; then
        cleanup
    fi
    
    show_usage
    
    log_success "Hailo8驱动Docker编译完成！"
}

# 运行主函数
main "$@"