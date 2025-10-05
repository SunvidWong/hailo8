#!/bin/bash

# Hailo8 Driver Installation Script for Container

set -e

# Colors for output
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

# 检查内核版本
check_kernel() {
    log_info "检查内核版本..."
    local kernel_version=$(uname -r)
    log_info "当前内核版本: $kernel_version"

    # 检查内核头文件
    if [[ ! -d "/lib/modules/$kernel_version/build" ]]; then
        log_warning "未找到内核头文件，尝试安装..."
        apt-get update && apt-get install -y "linux-headers-$kernel_version" || {
            log_warning "无法安装对应版本的内核头文件，使用通用头文件"
            apt-get install -y linux-headers-generic
        }
    fi
}

# 检查Hailo设备
check_hailo_device() {
    log_info "检查Hailo硬件设备..."

    # 检查PCIe设备
    if lspci | grep -i hailo; then
        log_success "检测到Hailo PCIe设备"
        return 0
    else
        log_warning "未检测到Hailo PCIe设备"
        return 1
    fi
}

# 编译和安装驱动
install_hailo_driver() {
    log_info "开始编译和安装Hailo驱动..."

    # 进入驱动源码目录
    cd /app/hailort-drivers-master/linux/pcie

    # 清理之前的编译结果
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
        log_success "找到编译好的驱动模块: hailo1x_pci.ko"
        ls -lh hailo1x_pci.ko
    else
        log_error "未找到编译好的驱动模块"
        exit 1
    fi

    # 安装驱动模块到系统
    log_info "安装驱动模块..."
    local kernel_version=$(uname -r)
    local modules_dir="/lib/modules/$kernel_version/kernel/drivers/misc"

    # 创建目标目录
    mkdir -p "$modules_dir"

    # 复制驱动模块
    cp hailo1x_pci.ko "$modules_dir/"

    # 更新模块依赖
    depmod -a

    # 加载驱动模块
    log_info "加载Hailo驱动模块..."
    modprobe hailo1x_pci

    # 检查驱动是否加载成功
    if lsmod | grep -q hailo1x_pci; then
        log_success "Hailo驱动加载成功"
    else
        log_error "Hailo驱动加载失败"
        # 显示错误信息
        dmesg | tail -10
        exit 1
    fi
}

# 设置设备权限
setup_device_permissions() {
    log_info "设置设备权限..."

    # 创建udev规则文件
    cat > /etc/udev/rules.d/99-hailo.rules << 'EOF'
# Hailo PCIe device permissions
KERNEL=="hailo[0-9]*", MODE="0666", GROUP="dialout"
SUBSYSTEM=="pci", ATTR{vendor}=="0x1e52", MODE="0666", GROUP="dialout"
EOF

    # 重新加载udev规则
    udevadm control --reload-rules
    udevadm trigger

    log_success "设备权限设置完成"
}

# 验证安装
verify_installation() {
    log_info "验证驱动安装..."

    # 检查驱动模块
    if lsmod | grep -q hailo1x_pci; then
        log_success "驱动模块已加载"
    else
        log_error "驱动模块未加载"
        return 1
    fi

    # 检查设备节点
    if [[ -e "/dev/hailo0" ]]; then
        log_success "设备节点 /dev/hailo0 已创建"
        ls -la /dev/hailo*
    else
        log_warning "设备节点未创建，可能需要重启系统"
    fi

    # 检查驱动信息
    log_info "驱动模块信息:"
    modinfo hailo1x_pci | head -10
}

# 主函数
main() {
    log_info "开始安装Hailo8驱动..."

    # 检查是否以root权限运行
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi

    # 执行安装步骤
    check_kernel
    check_hailo_device || {
        log_warning "未检测到Hailo硬件，继续安装驱动以便后续使用"
    }
    install_hailo_driver
    setup_device_permissions
    verify_installation

    log_success "Hailo8驱动安装完成！"
    log_info "设备节点: /dev/hailo*"
    log_info "可以使用 'lspci | grep hailo' 检查硬件状态"
}

# 如果脚本被直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi