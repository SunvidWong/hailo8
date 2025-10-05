#!/bin/bash

# Hailo8 PCIe驱动自动编译脚本
# 适用于Ubuntu/Debian和CentOS/RHEL系统

set -e  # 遇到错误立即退出

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户编译，仅在安装时使用sudo"
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log_info "检测到操作系统: $OS $VER"
}

# 安装编译依赖
install_dependencies() {
    log_info "安装编译依赖..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        sudo apt update
        sudo apt install -y build-essential linux-headers-$(uname -r) make gcc dkms
        log_success "Ubuntu/Debian依赖安装完成"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y kernel-devel-$(uname -r) make gcc dkms
        log_success "CentOS/RHEL依赖安装完成"
    elif [[ "$OS" == *"Fedora"* ]]; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y kernel-devel-$(uname -r) make gcc dkms
        log_success "Fedora依赖安装完成"
    else
        log_warning "未识别的操作系统，请手动安装编译依赖"
        log_info "需要安装: build-essential, linux-headers, make, gcc, dkms"
    fi
}

# 检查内核头文件
check_kernel_headers() {
    local kernel_version=$(uname -r)
    local headers_path="/lib/modules/$kernel_version/build"
    
    if [[ -d "$headers_path" ]]; then
        log_success "内核头文件检查通过: $headers_path"
    else
        log_error "内核头文件未找到: $headers_path"
        log_info "请安装对应版本的内核头文件"
        exit 1
    fi
}

# 编译驱动
compile_driver() {
    log_info "开始编译Hailo8 PCIe驱动..."
    
    # 检查源码目录
    if [[ ! -d "hailort-drivers-master/linux/pcie" ]]; then
        log_error "未找到驱动源码目录，请确保在正确的目录下运行脚本"
        exit 1
    fi
    
    cd hailort-drivers-master/linux/pcie
    
    # 清理之前的编译结果
    log_info "清理之前的编译结果..."
    make clean 2>/dev/null || true
    
    # 编译驱动
    log_info "编译驱动模块..."
    if make all; then
        log_success "驱动编译成功"
    else
        log_error "驱动编译失败"
        exit 1
    fi
    
    # 检查编译结果
    if [[ -f "hailo1x_pci.ko" ]]; then
        log_success "驱动模块生成成功: hailo1x_pci.ko"
        ls -la hailo1x_pci.ko
    else
        log_error "驱动模块未生成"
        exit 1
    fi
    
    cd - > /dev/null
}

# 安装驱动
install_driver() {
    log_info "安装驱动..."
    
    cd hailort-drivers-master/linux/pcie
    
    if sudo make install; then
        log_success "驱动安装成功"
    else
        log_error "驱动安装失败"
        exit 1
    fi
    
    cd - > /dev/null
}

# 加载驱动
load_driver() {
    log_info "加载驱动模块..."
    
    # 卸载可能已存在的驱动
    sudo modprobe -r hailo1x_pci 2>/dev/null || true
    
    # 加载新驱动
    if sudo modprobe hailo1x_pci; then
        log_success "驱动加载成功"
    else
        log_error "驱动加载失败"
        exit 1
    fi
}

# 验证安装
verify_installation() {
    log_info "验证驱动安装..."
    
    # 检查驱动是否加载
    if lsmod | grep -q hailo1x_pci; then
        log_success "驱动已成功加载"
        lsmod | grep hailo
    else
        log_warning "驱动未在lsmod中找到"
    fi
    
    # 检查设备节点
    if ls /dev/hailo* 2>/dev/null; then
        log_success "设备节点创建成功"
    else
        log_warning "未找到设备节点，可能需要连接Hailo设备"
    fi
    
    # 显示驱动信息
    log_info "驱动模块信息:"
    modinfo hailo1x_pci 2>/dev/null || log_warning "无法获取驱动信息"
}

# 主函数
main() {
    log_info "开始Hailo8 PCIe驱动编译安装流程"
    
    check_root
    detect_os
    
    # 解析命令行参数
    INSTALL_DEPS=true
    COMPILE_ONLY=false
    INSTALL_DRIVER=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-deps)
                INSTALL_DEPS=false
                shift
                ;;
            --compile-only)
                COMPILE_ONLY=true
                INSTALL_DRIVER=false
                shift
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --no-deps      跳过依赖安装"
                echo "  --compile-only 仅编译，不安装"
                echo "  --help         显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行编译流程
    if [[ "$INSTALL_DEPS" == true ]]; then
        install_dependencies
    fi
    
    check_kernel_headers
    compile_driver
    
    if [[ "$COMPILE_ONLY" == false ]] && [[ "$INSTALL_DRIVER" == true ]]; then
        install_driver
        load_driver
        verify_installation
    fi
    
    log_success "Hailo8驱动编译安装完成！"
    
    if [[ "$COMPILE_ONLY" == true ]]; then
        log_info "编译完成，驱动文件位于: hailort-drivers-master/linux/pcie/hailo1x_pci.ko"
        log_info "如需安装，请运行: sudo make install && sudo modprobe hailo1x_pci"
    fi
}

# 运行主函数
main "$@"