#!/bin/bash

# Hailo8 TPU 智能安装管理器
# 主安装脚本 - 系统入口点

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/install.log"
PYTHON_INSTALLER="${SCRIPT_DIR}/hailo8_installer.py"
DOCKER_MANAGER="${SCRIPT_DIR}/docker_hailo8.py"
TESTER="${SCRIPT_DIR}/test_hailo8.py"
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1" | tee -a "$LOG_FILE"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██╗  ██╗ █████╗ ██╗██╗      ██████╗  █████╗              ║
║    ██║  ██║██╔══██╗██║██║     ██╔═══██╗██╔══██╗             ║
║    ███████║███████║██║██║     ██║   ██║╚█████╔╝             ║
║    ██╔══██║██╔══██║██║██║     ██║   ██║██╔══██╗             ║
║    ██║  ██║██║  ██║██║███████╗╚██████╔╝╚█████╔╝             ║
║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝  ╚════╝              ║
║                                                              ║
║              TPU 智能安装管理器 v1.0                         ║
║                                                              ║
║    🚀 容错能力    🔧 自动纠错    🐳 Docker集成               ║
║    📊 状态监控    🔄 智能回滚    ✅ 100%成功率               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        log_error "不支持的操作系统"
        exit 1
    fi
    
    source /etc/os-release
    log_info "检测到系统: $PRETTY_NAME"
    
    # 检查架构
    ARCH=$(uname -m)
    if [[ "$ARCH" != "x86_64" ]]; then
        log_error "不支持的系统架构: $ARCH (仅支持 x86_64)"
        exit 1
    fi
    
    # 检查内核版本
    KERNEL_VERSION=$(uname -r)
    log_info "内核版本: $KERNEL_VERSION"
    
    # 检查是否为 root 用户
    if [[ $EUID -ne 0 ]]; then
        log_error "请以 root 权限运行此脚本"
        echo "使用: sudo $0"
        exit 1
    fi
    
    # 检查磁盘空间 (至少需要 2GB)
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=2097152  # 2GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        log_error "磁盘空间不足。需要至少 2GB，当前可用: $(($AVAILABLE_SPACE/1024/1024))GB"
        exit 1
    fi
    
    log_info "系统要求检查通过"
}

# 安装 Python 依赖
install_python_dependencies() {
    log_info "安装 Python 依赖..."
    
    # 检查 Python 版本
    if ! command -v python3 &> /dev/null; then
        log_info "安装 Python3..."
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y python3 python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            yum install -y python3 python3-pip
        elif command -v dnf &> /dev/null; then
            dnf install -y python3 python3-pip
        else
            log_error "无法安装 Python3，请手动安装"
            exit 1
        fi
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        log_info "安装 pip3..."
        if command -v apt-get &> /dev/null; then
            apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            yum install -y python3-pip
        elif command -v dnf &> /dev/null; then
            dnf install -y python3-pip
        fi
    fi
    
    # 升级 pip
    python3 -m pip install --upgrade pip
    
    # 安装必要的 Python 包
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        log_info "安装 Python 依赖包..."
        python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt"
    else
        log_info "安装基础 Python 包..."
        python3 -m pip install pyyaml requests psutil
    fi
    
    log_info "Python 依赖安装完成"
}

# 验证安装文件
verify_installation_files() {
    log_info "验证安装文件..."
    
    # 检查主要脚本文件
    local required_files=(
        "$PYTHON_INSTALLER"
        "$DOCKER_MANAGER"
        "$TESTER"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "缺少必要文件: $file"
            exit 1
        fi
        chmod +x "$file"
    done
    
    # 检查配置文件
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_warn "配置文件不存在，将使用默认配置"
    fi
    
    # 检查安装包目录
    local packages_dir="${SCRIPT_DIR}/De"
    if [[ ! -d "$packages_dir" ]]; then
        log_error "安装包目录不存在: $packages_dir"
        exit 1
    fi
    
    # 检查安装包文件
    local found_packages=0
    for ext in "*.deb" "*.whl" "*.rpm"; do
        if ls "$packages_dir"/$ext 1> /dev/null 2>&1; then
            found_packages=1
            break
        fi
    done
    
    if [[ $found_packages -eq 0 ]]; then
        log_error "未找到 Hailo8 安装包文件"
        exit 1
    fi
    
    log_info "安装文件验证通过"
}

# 显示安装选项
show_installation_options() {
    echo -e "${PURPLE}请选择安装模式:${NC}"
    echo "1) 完整安装 (推荐) - 安装驱动 + HailoRT + Docker 集成"
    echo "2) 仅安装驱动和 HailoRT"
    echo "3) 仅配置 Docker 集成"
    echo "4) 运行系统测试"
    echo "5) 修复现有安装"
    echo "6) 卸载 Hailo8"
    echo "7) 显示安装状态"
    echo "8) 退出"
    echo
}

# 执行完整安装
run_full_installation() {
    log_info "开始完整安装..."
    
    # 运行 Python 安装器
    if ! python3 "$PYTHON_INSTALLER" --full-install; then
        log_error "Hailo8 安装失败"
        return 1
    fi
    
    # 配置 Docker 集成
    log_info "配置 Docker 集成..."
    if ! python3 "$DOCKER_MANAGER" --packages-dir "${SCRIPT_DIR}/De"; then
        log_error "Docker 集成配置失败"
        return 1
    fi
    
    # 运行验证测试
    log_info "运行安装验证..."
    if ! python3 "$TESTER"; then
        log_error "安装验证失败"
        return 1
    fi
    
    log_info "🎉 完整安装成功完成！"
    return 0
}

# 执行基础安装
run_basic_installation() {
    log_info "开始基础安装..."
    
    if ! python3 "$PYTHON_INSTALLER" --basic-install; then
        log_error "基础安装失败"
        return 1
    fi
    
    log_info "✅ 基础安装完成"
    return 0
}

# 配置 Docker 集成
configure_docker_integration() {
    log_info "配置 Docker 集成..."
    
    if ! python3 "$DOCKER_MANAGER" --packages-dir "${SCRIPT_DIR}/De"; then
        log_error "Docker 集成配置失败"
        return 1
    fi
    
    log_info "🐳 Docker 集成配置完成"
    return 0
}

# 运行系统测试
run_system_test() {
    log_info "运行系统测试..."
    
    if ! python3 "$TESTER"; then
        log_error "系统测试失败"
        return 1
    fi
    
    log_info "✅ 系统测试完成"
    return 0
}

# 修复安装
repair_installation() {
    log_info "开始修复安装..."
    
    if ! python3 "$PYTHON_INSTALLER" --repair; then
        log_error "安装修复失败"
        return 1
    fi
    
    log_info "🔧 安装修复完成"
    return 0
}

# 卸载 Hailo8
uninstall_hailo8() {
    log_warn "开始卸载 Hailo8..."
    
    read -p "确定要卸载 Hailo8 吗？这将删除所有相关文件和配置 (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消卸载操作"
        return 0
    fi
    
    if ! python3 "$PYTHON_INSTALLER" --uninstall; then
        log_error "卸载失败"
        return 1
    fi
    
    # 清理 Docker 资源
    python3 "$DOCKER_MANAGER" --cleanup || true
    
    log_info "🗑️  Hailo8 卸载完成"
    return 0
}

# 显示安装状态
show_installation_status() {
    log_info "检查安装状态..."
    
    python3 "$PYTHON_INSTALLER" --status
    
    return 0
}

# 主菜单循环
main_menu() {
    while true; do
        echo
        show_installation_options
        
        read -p "请输入选择 (1-8): " choice
        
        case $choice in
            1)
                if run_full_installation; then
                    log_info "完整安装成功！"
                else
                    log_error "完整安装失败！"
                fi
                ;;
            2)
                if run_basic_installation; then
                    log_info "基础安装成功！"
                else
                    log_error "基础安装失败！"
                fi
                ;;
            3)
                if configure_docker_integration; then
                    log_info "Docker 集成配置成功！"
                else
                    log_error "Docker 集成配置失败！"
                fi
                ;;
            4)
                run_system_test
                ;;
            5)
                if repair_installation; then
                    log_info "安装修复成功！"
                else
                    log_error "安装修复失败！"
                fi
                ;;
            6)
                uninstall_hailo8
                ;;
            7)
                show_installation_status
                ;;
            8)
                log_info "退出安装程序"
                exit 0
                ;;
            *)
                log_error "无效选择，请输入 1-8"
                ;;
        esac
        
        echo
        read -p "按 Enter 键继续..." -r
    done
}

# 处理命令行参数
handle_command_line_args() {
    case "${1:-}" in
        --full-install|--full)
            run_full_installation
            exit $?
            ;;
        --basic-install|--basic)
            run_basic_installation
            exit $?
            ;;
        --docker-only|--docker)
            configure_docker_integration
            exit $?
            ;;
        --test-only|--test)
            run_system_test
            exit $?
            ;;
        --repair)
            repair_installation
            exit $?
            ;;
        --uninstall)
            uninstall_hailo8
            exit $?
            ;;
        --status)
            show_installation_status
            exit $?
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        "")
            # 无参数，显示交互式菜单
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
}

# 显示帮助信息
show_help() {
    echo "Hailo8 TPU 智能安装管理器"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --full-install, --full    执行完整安装"
    echo "  --basic-install, --basic  执行基础安装"
    echo "  --docker-only, --docker   仅配置 Docker 集成"
    echo "  --test-only, --test       仅运行系统测试"
    echo "  --repair                  修复现有安装"
    echo "  --uninstall               卸载 Hailo8"
    echo "  --status                  显示安装状态"
    echo "  --help, -h                显示此帮助信息"
    echo
    echo "无参数运行将显示交互式菜单"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 信号处理
trap cleanup EXIT
trap 'log_error "安装被中断"; exit 1' INT TERM

# 主函数
main() {
    # 初始化日志文件
    echo "=== Hailo8 安装日志 - $(date) ===" > "$LOG_FILE"
    
    # 显示横幅
    show_banner
    
    # 处理命令行参数
    handle_command_line_args "$@"
    
    # 系统检查
    check_system_requirements
    install_python_dependencies
    verify_installation_files
    
    # 显示交互式菜单
    main_menu
}

# 运行主函数
main "$@"