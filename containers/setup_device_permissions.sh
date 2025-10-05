#!/bin/bash

# Hailo8设备权限配置脚本
# 设置Docker容器访问Hailo设备的权限

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

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi

    log_success "Docker检查通过"
}

# 检测Hailo硬件
detect_hailo_hardware() {
    log_info "检测Hailo硬件设备..."

    # 检查PCIe设备
    local pcie_devices=$(lspci -d 1e52: 2>/dev/null)
    if [[ -n "$pcie_devices" ]]; then
        log_success "检测到Hailo PCIe设备:"
        echo "$pcie_devices"
        return 0
    else
        log_warning "未检测到Hailo PCIe设备"
        return 1
    fi
}

# 创建Hailo用户组
create_hailo_group() {
    log_info "创建Hailo用户组..."

    if ! getent group hailo >/dev/null 2>&1; then
        groupadd hailo
        log_success "创建hailo用户组"
    else
        log_info "hailo用户组已存在"
    fi
}

# 设置udev规则
setup_udev_rules() {
    log_info "设置udev规则..."

    # 备份现有规则
    if [[ -f "/etc/udev/rules.d/99-hailo.rules" ]]; then
        cp "/etc/udev/rules.d/99-hailo.rules" "/etc/udev/rules.d/99-hailo.rules.backup"
        log_info "备份现有udev规则"
    fi

    # 创建Hailo设备udev规则
    cat > /etc/udev/rules.d/99-hailo.rules << 'EOF'
# Hailo PCIe设备权限规则
# 为Hailo设备设置适当的权限

# PCIe设备
KERNEL=="hailo[0-9]*", MODE="0666", GROUP="hailo"
SUBSYSTEM=="pci", ATTR{vendor}=="0x1e52", MODE="0666", GROUP="hailo"

# 字符设备
SUBSYSTEM=="char", ATTR{dev}=="hailo[0-9]*", MODE="0666", GROUP="hailo"

# USB设备 (如果适用)
SUBSYSTEM=="usb", ATTR{idVendor}=="1e52", MODE="0666", GROUP="hailo"

# DRM设备 (GPU相关)
SUBSYSTEM=="drm", GROUP="video", MODE="0666"

# VFIO设备 (虚拟化)
SUBSYSTEM=="vfio", GROUP="kvm", MODE="0666"
EOF

    # 重新加载udev规则
    udevadm control --reload-rules
    udevadm trigger

    log_success "udev规则设置完成"
}

# 设置内核模块权限
setup_kernel_module_permissions() {
    log_info "设置内核模块权限..."

    # 创建modprobe配置
    cat > /etc/modprobe.d/hailo.conf << 'EOF'
# Hailo内核模块配置
options hailo1x_pci no_power_mode=N
options hailo1x_pci debug_level=2
EOF

    log_success "内核模块配置完成"
}

# 配置Docker用户权限
setup_docker_permissions() {
    log_info "配置Docker用户权限..."

    # 获取当前用户
    local current_user=${SUDO_USER:-$(whoami)}

    if [[ "$current_user" != "root" ]]; then
        # 将用户添加到相关组
        usermod -a -G docker,hailo,video,kvm "$current_user"

        log_success "用户 $current_user 已添加到相关组:"
        echo "  - docker (Docker访问)"
        echo "  - hailo (Hailo设备访问)"
        echo "  - video (视频设备访问)"
        echo "  - kvm (虚拟化支持)"

        log_warning "请重新登录或运行以下命令使权限生效:"
        echo "  newgrp docker"
        echo "  newgrp hailo"
        echo "  newgrp video"
        echo "  newgrp kvm"
    else
        log_info "当前为root用户，跳过用户权限设置"
    fi
}

# 创建设备目录
create_device_directories() {
    log_info "创建设备目录..."

    # 创建必要的目录
    mkdir -p /dev/hailo
    mkdir -p /var/run/hailo
    mkdir -p /opt/hailo

    # 设置权限
    chmod 755 /dev/hailo
    chmod 755 /var/run/hailo
    chmod 755 /opt/hailo

    chown root:hailo /dev/hailo
    chown root:hailo /var/run/hailo
    chown root:hailo /opt/hailo

    log_success "设备目录创建完成"
}

# 测试设备访问
test_device_access() {
    log_info "测试设备访问权限..."

    # 检查设备节点
    local device_found=false
    for device in /dev/hailo0 /dev/hailo1; do
        if [[ -e "$device" ]]; then
            log_success "找到设备节点: $device"
            ls -la "$device"
            device_found=true
        fi
    done

    if [[ "$device_found" == false ]]; then
        log_warning "未找到Hailo设备节点，这可能是正常的（如果驱动未加载）"
    fi

    # 检查PCIe设备权限
    local pcie_devices=$(lspci -d 1e52: 2>/dev/null)
    if [[ -n "$pcie_devices" ]]; then
        log_success "PCIe设备检测正常"
    fi
}

# 安装Hailo驱动 (可选)
install_hailo_driver() {
    log_info "是否安装Hailo驱动? (y/N)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "开始安装Hailo驱动..."

        # 检查驱动源码
        if [[ -d "./hailort-drivers-master" ]]; then
            cd hailort-drivers-master/linux/pcie

            # 编译和安装驱动
            make clean 2>/dev/null || true
            if make all; then
                make install
                modprobe hailo1x_pci
                log_success "Hailo驱动安装完成"
            else
                log_error "驱动编译失败"
            fi
        else
            log_error "未找到驱动源码目录 hailort-drivers-master"
        fi
    else
        log_info "跳过驱动安装"
    fi
}

# 创建systemd服务 (可选)
create_systemd_service() {
    log_info "是否创建systemd服务? (y/N)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "创建Hailo设备服务..."

        cat > /etc/systemd/system/hailo-device.service << 'EOF'
[Unit]
Description=Hailo Device Setup Service
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/hailo-device-setup
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

        # 创建设备设置脚本
        cat > /usr/local/bin/hailo-device-setup << 'EOF'
#!/bin/bash
# Hailo设备自动设置脚本

# 加载内核模块
modprobe hailo1x_pci 2>/dev/null || true

# 设置设备权限
chown root:hailo /dev/hailo* 2>/dev/null || true
chmod 0666 /dev/hailo* 2>/dev/null || true

# 创建运行时目录
mkdir -p /var/run/hailo
chown root:hailo /var/run/hailo
EOF

        chmod +x /usr/local/bin/hailo-device-setup

        # 启用服务
        systemctl enable hailo-device.service
        systemctl start hailo-device.service

        log_success "systemd服务创建完成"
    else
        log_info "跳过systemd服务创建"
    fi
}

# 显示配置摘要
show_summary() {
    log_info "设备权限配置完成！"
    echo ""
    echo "配置摘要:"
    echo "  ✅ udev规则已配置: /etc/udev/rules.d/99-hailo.rules"
    echo "  ✅ 内核模块配置: /etc/modprobe.d/hailo.conf"
    echo "  ✅ 用户权限已设置"
    echo "  ✅ 设备目录已创建"
    echo ""
    echo "下一步:"
    echo "  1. 重新登录或运行 newgrp 命令使权限生效"
    echo "  2. 运行 docker-compose up -d 启动服务"
    echo "  3. 访问 http://localhost:8000 查看API文档"
    echo ""
    echo "故障排除:"
    echo "  - 检查设备权限: ls -la /dev/hailo*"
    echo "  - 检查驱动状态: lsmod | grep hailo"
    echo "  - 查看内核日志: dmesg | grep hailo"
}

# 主函数
main() {
    log_info "开始配置Hailo8设备权限..."
    echo ""

    check_root
    check_docker
    detect_hailo_hardware || log_warning "继续设置权限配置"

    create_hailo_group
    setup_udev_rules
    setup_kernel_module_permissions
    setup_docker_permissions
    create_device_directories
    test_device_access

    # 可选步骤
    install_hailo_driver
    create_systemd_service

    show_summary

    log_success "Hailo8设备权限配置完成！"
}

# 运行主函数
main "$@"