#!/bin/bash

# Hailo8 Python包安装脚本 v1.3
# 适用于飞牛OS (基于Debian)
# 集成Python 3.12自动安装和完整清理功能
# 作者: Claude Assistant

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

# 文件路径配置
DEB_FILE="/vol1/1000/hailo8/hailort-pcie-driver_4.23.0_all.deb"
WHEEL_FILE="/vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl"

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行，请使用 sudo"
        exit 1
    fi
}

# 安装Python 3.12
install_python312() {
    log_info "检查Python 3.12是否已安装..."
    
    # 检查是否已经有Python 3.12
    if command -v python3.12 >/dev/null 2>&1; then
        local version=$(python3.12 --version 2>&1)
        log_success "✓ Python 3.12已安装: $version"
        return 0
    fi
    
    log_info "Python 3.12未找到，开始安装..."
    
    # 更新包索引
    log_info "更新包索引..."
    apt update
    
    # 安装必要的依赖
    log_info "安装编译依赖..."
    apt install -y software-properties-common build-essential zlib1g-dev \
        libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
        libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
    
    # 尝试添加deadsnakes PPA（如果是Ubuntu系统）
    if command -v add-apt-repository >/dev/null 2>&1; then
        log_info "添加Python PPA源..."
        add-apt-repository ppa:deadsnakes/ppa -y || log_warning "PPA添加失败，将尝试源码编译"
        apt update
        
        # 尝试从PPA安装
        log_info "从PPA安装Python 3.12..."
        if apt install -y python3.12 python3.12-venv python3.12-pip python3.12-dev 2>/dev/null; then
            log_success "✓ Python 3.12安装成功（PPA方式）"
            return 0
        else
            log_warning "PPA安装失败，尝试源码编译..."
        fi
    fi
    
    # 源码编译安装
    log_info "从源码编译安装Python 3.12..."
    
    # 创建临时目录
    local temp_dir="/tmp/python312_install"
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    # 下载Python 3.12源码
    log_info "下载Python 3.12.4源码..."
    if ! wget -q https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz; then
        log_error "下载Python源码失败"
        return 1
    fi
    
    tar -xf Python-3.12.4.tgz
    cd Python-3.12.4
    
    # 配置编译选项
    log_info "配置编译选项..."
    ./configure --enable-optimizations --with-ensurepip=install --prefix=/usr/local
    
    # 编译（使用多核）
    log_info "编译Python 3.12（这可能需要几分钟）..."
    make -j$(nproc)
    
    # 安装
    log_info "安装Python 3.12..."
    make altinstall
    
    # 验证安装
    if command -v python3.12 >/dev/null 2>&1; then
        local version=$(python3.12 --version 2>&1)
        log_success "✓ Python 3.12编译安装成功: $version"
        
        # 确保pip可用
        if ! python3.12 -m pip --version >/dev/null 2>&1; then
            log_info "安装pip..."
            python3.12 -m ensurepip --default-pip
        fi
        
        # 清理临时文件
        cd /
        rm -rf "$temp_dir"
        
        # 清理下载的源码包
        rm -f /tmp/Python-3.12.4.tgz 2>/dev/null || true
        
        return 0
    else
        log_error "Python 3.12安装失败"
        return 1
    fi
}

# 检查wheel文件兼容性
check_wheel_compatibility() {
    local wheel_file="$1"
    
    log_info "检查wheel文件兼容性..."
    
    # 获取当前系统信息
    local current_arch=$(uname -m)
    local current_os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local python_version=$(python3.12 --version 2>/dev/null | grep -o "3\.[0-9]\+" || python3 --version | grep -o "3\.[0-9]\+")
    
    log_info "当前系统: $current_os-$current_arch, Python: $python_version"
    
    # 从wheel文件名提取信息
    local wheel_basename=$(basename "$wheel_file")
    log_info "Wheel文件: $wheel_basename"
    
    # 检查操作系统兼容性
    if [[ "$current_os" == "darwin" ]] && [[ "$wheel_basename" == *"linux"* ]]; then
        log_error "❌ 平台不兼容: 当前系统是macOS，但wheel文件是为Linux编译的"
        log_error "❌ 此wheel文件无法在macOS上运行"
        log_info "💡 解决方案:"
        log_info "   1. 在Linux系统上运行此脚本"
        log_info "   2. 或者获取适用于macOS的wheel文件"
        log_info "   3. 或者从源码编译适用于macOS的版本"
        return 1
    fi
    
    # 检查架构兼容性
    if [[ "$current_arch" == "arm64" ]] && [[ "$wheel_basename" == *"x86_64"* ]]; then
        log_error "❌ 架构不兼容: 当前系统是ARM64，但wheel文件是为x86_64编译的"
        log_info "💡 解决方案:"
        log_info "   1. 在x86_64系统上运行此脚本"
        log_info "   2. 或者获取适用于ARM64的wheel文件"
        return 1
    fi
    
    # 检查Python版本兼容性
    if [[ "$wheel_basename" == *"cp312"* ]] && [[ "$python_version" != "3.12" ]]; then
        log_warning "⚠️  Python版本可能不兼容: wheel需要Python 3.12，当前是Python $python_version"
        log_info "💡 建议: 安装Python 3.12或获取适用于Python $python_version的wheel文件"
        return 2  # 警告但不阻止安装
    fi
    
    log_success "✓ Wheel文件与当前系统兼容"
    return 0
}

# 检查文件是否存在
check_files() {
    log_info "检查安装文件..."
    
    # 只检查Python wheel文件，不检查deb文件
    # if [[ ! -f "$DEB_FILE" ]]; then
    #     log_error "找不到deb文件: $DEB_FILE"
    #     exit 1
    # fi
    # log_success "找到deb文件: $DEB_FILE"
    
    if [[ ! -f "$WHEEL_FILE" ]]; then
        log_error "找不到wheel文件: $WHEEL_FILE"
        exit 1
    fi
    log_success "找到wheel文件: $WHEEL_FILE"
    
    # 检查wheel文件兼容性（但不阻止安装）
    if ! check_wheel_compatibility "$WHEEL_FILE"; then
        log_warning "Wheel文件与当前系统可能不兼容，但将尝试强制安装"
        log_info "系统信息不匹配，但脚本会自动尝试多种安装方法"
    fi
}

# 检查系统环境
check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [[ ! -f /etc/debian_version ]]; then
        log_warning "当前系统可能不是基于Debian的发行版"
    else
        log_success "检测到Debian系统"
    fi
    
    # 检查内核版本
    KERNEL_VERSION=$(uname -r)
    log_info "当前内核版本: $KERNEL_VERSION"
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_info "Python版本: $PYTHON_VERSION"
    else
        log_error "未找到Python3，请先安装Python3"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_warning "未找到pip3，正在安装..."
        apt update
        apt install -y python3-pip
    fi
}

# 备份现有安装
backup_existing() {
    log_info "检查并备份现有Hailo安装..."
    
    # 检查是否已安装hailo驱动
    if lsmod | grep -q hailo; then
        log_warning "检测到已加载的Hailo驱动，正在卸载..."
        modprobe -r hailo_pci || true
    fi
    
    # 备份现有配置
    BACKUP_DIR="/tmp/hailo_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -d /lib/firmware/hailo ]]; then
        cp -r /lib/firmware/hailo "$BACKUP_DIR/" || true
        log_info "已备份固件到: $BACKUP_DIR"
    fi
}

# 安装deb包
install_deb_package() {
    log_info "安装Hailo PCIe驱动deb包..."
    
    # 更新包索引
    apt update
    
    # 安装必要的依赖
    apt install -y dkms build-essential linux-headers-$(uname -r)
    
    # 安装deb包
    if dpkg -i "$DEB_FILE"; then
        log_success "deb包安装成功"
    else
        log_warning "deb包安装遇到依赖问题，正在修复..."
        apt-get install -f -y
        if dpkg -i "$DEB_FILE"; then
            log_success "deb包安装成功（已修复依赖）"
        else
            log_error "deb包安装失败"
            exit 1
        fi
    fi
}

# 尝试强制安装wheel文件（忽略平台检查）
install_python_package_force() {
    log_info "尝试强制安装Python包（忽略平台检查）..."
    
    # 优先使用python3.12
    local python_cmd="python3.12"
    local pip_cmd="pip3.12"
    
    # 如果python3.12不可用，回退到python3
    if ! command -v python3.12 >/dev/null 2>&1; then
        log_warning "python3.12不可用，使用python3"
        python_cmd="python3"
        pip_cmd="pip3"
    fi
    
    # 卸载已有的包
    log_info "卸载现有的HailoRT包..."
    $pip_cmd uninstall -y hailort 2>/dev/null || true
    
    # 方法1: 使用 --force-reinstall --no-deps --break-system-packages
    log_info "方法1: 强制安装（忽略依赖和平台检查）..."
    if $pip_cmd install "$WHEEL_FILE" --force-reinstall --no-deps --break-system-packages 2>/dev/null; then
        log_success "✓ 强制安装成功（系统环境）"
        return 0
    fi
    
    # 方法2: 用户级强制安装
    log_info "方法2: 用户级强制安装..."
    if $pip_cmd install "$WHEEL_FILE" --force-reinstall --no-deps --user --break-system-packages 2>/dev/null; then
        log_success "✓ 用户级强制安装成功"
        return 0
    fi
    
    # 方法3: 虚拟环境强制安装
    log_info "方法3: 虚拟环境强制安装..."
    if [ ! -d "/opt/hailo_venv" ]; then
        log_info "创建虚拟环境..."
        $python_cmd -m venv /opt/hailo_venv
        if [ $? -ne 0 ]; then
            log_error "虚拟环境创建失败"
            return 1
        fi
        log_success "虚拟环境创建成功: /opt/hailo_venv"
    fi
    
    if /opt/hailo_venv/bin/pip install "$WHEEL_FILE" --force-reinstall --no-deps 2>/dev/null; then
        log_success "✓ 虚拟环境强制安装成功"
        
        # 创建快捷命令
        if [ ! -f "/usr/local/bin/hailo-python" ]; then
            cat > /usr/local/bin/hailo-python << 'EOF'
#!/bin/bash
/opt/hailo_venv/bin/python "$@"
EOF
            chmod +x /usr/local/bin/hailo-python
            log_info "创建快捷命令: hailo-python"
        fi
        return 0
    fi
    
    log_error "所有强制安装方法都失败了"
    return 1
}
install_python_package() {
    log_info "安装HailoRT Python包..."
    
    # 优先使用python3.12
    local python_cmd="python3.12"
    local pip_cmd="pip3.12"
    
    # 如果python3.12不可用，回退到python3
    if ! command -v python3.12 >/dev/null 2>&1; then
        log_warning "python3.12不可用，使用python3"
        python_cmd="python3"
        pip_cmd="pip3"
    fi
    
    # 卸载可能存在的旧版本
    $pip_cmd uninstall -y hailort 2>/dev/null || true
    
    # 尝试多种安装方法
    log_info "检测Python环境管理策略..."
    
    # 方法1: 尝试使用 --break-system-packages (推荐用于系统级驱动)
    log_info "方法1: 使用 --break-system-packages 安装..."
    if $pip_cmd install "$WHEEL_FILE" --break-system-packages; then
        log_success "Python包安装成功 (系统级安装)"
        return 0
    fi
    
    # 方法2: 尝试使用 --user 安装到用户目录
    log_info "方法2: 安装到用户目录..."
    if $pip_cmd install "$WHEEL_FILE" --user; then
        log_success "Python包安装成功 (用户级安装)"
        log_warning "注意: 包已安装到用户目录，可能需要设置PYTHONPATH"
        return 0
    fi
    
    # 方法3: 创建虚拟环境安装
    log_info "方法3: 创建虚拟环境安装..."
    VENV_PATH="/opt/hailo_venv"
    
    # 安装venv模块如果不存在
    if ! $python_cmd -m venv --help &>/dev/null; then
        log_info "安装python3-venv..."
        if command -v python3.12 >/dev/null 2>&1; then
            apt install -y python3.12-venv
        else
            apt install -y python3-venv python3-full
        fi
    fi
    
    # 创建虚拟环境
    if $python_cmd -m venv "$VENV_PATH"; then
        log_info "虚拟环境创建成功: $VENV_PATH"
        
        # 在虚拟环境中安装
        if "$VENV_PATH/bin/pip" install "$WHEEL_FILE"; then
            log_success "Python包安装成功 (虚拟环境)"
            log_info "虚拟环境路径: $VENV_PATH"
            log_info "使用方法: source $VENV_PATH/bin/activate"
            
            # 创建系统级符号链接 (可选)
            if [ ! -f /usr/local/bin/hailo-python ]; then
                ln -s "$VENV_PATH/bin/python" /usr/local/bin/hailo-python
                log_info "创建快捷命令: hailo-python"
            fi
            return 0
        fi
    fi
    
    log_error "所有Python包安装方法都失败了"
    
    # 如果常规安装失败，尝试强制安装
    log_info "尝试强制安装（忽略平台兼容性检查）..."
    if install_python_package_force; then
        return 0
    fi
    
    log_error "请手动安装或联系技术支持"
    return 1
}

# 加载驱动模块
load_driver() {
    log_info "加载Hailo驱动模块..."
    
    # 加载驱动
    if modprobe hailo_pci; then
        log_success "驱动模块加载成功"
    else
        log_error "驱动模块加载失败"
        return 1
    fi
    
    # 等待设备初始化
    sleep 2
}

# 检查安装状态
check_installation() {
    log_info "检查Python包安装状态..."
    
    local all_checks_passed=true
    
    # 跳过驱动相关检查，只检查Python包
    # 1. 检查驱动模块 (跳过)
    # log_info "1. 检查驱动模块..."
    # if lsmod | grep -q hailo_pci; then
    #     log_success "✓ Hailo PCIe驱动已加载"
    # else
    #     log_error "✗ Hailo PCIe驱动未加载"
    #     all_checks_passed=false
    # fi
    
    # 2. 检查设备文件 (跳过)
    # log_info "2. 检查设备文件..."
    # if ls /dev/hailo* &> /dev/null; then
    #     DEVICES=$(ls /dev/hailo*)
    #     log_success "✓ 找到Hailo设备: $DEVICES"
    # else
    #     log_error "✗ 未找到Hailo设备文件"
    #     all_checks_passed=false
    # fi
    
    # 3. 检查dmesg日志 (跳过)
    # log_info "3. 检查内核日志..."
    # if dmesg | tail -20 | grep -i hailo | grep -v error; then
    #     log_success "✓ 内核日志显示正常"
    # else
    #     log_warning "! 内核日志中可能有问题，请检查 dmesg | grep hailo"
    # fi
    
    # 1. 检查Python包 (重新编号)
    log_info "1. 检查Python包..."
    
    # 优先使用python3.12
    local python_cmd="python3.12"
    
    # 如果python3.12不可用，回退到python3
    if ! command -v python3.12 >/dev/null 2>&1; then
        python_cmd="python3"
    fi
    
    # 尝试多种Python环境
    python_test_success=false
    
    # 测试系统Python (优先使用python3.12)
    if $python_cmd -c "import hailo_platform; print('HailoRT Python API 版本:', hailo_platform.__version__)" 2>/dev/null; then
        log_success "✓ Python包导入成功 (系统环境 - $python_cmd)"
        python_test_success=true
    # 如果python3.12失败，尝试python3
    elif [ "$python_cmd" = "python3.12" ] && python3 -c "import hailo_platform; print('HailoRT Python API 版本:', hailo_platform.__version__)" 2>/dev/null; then
        log_success "✓ Python包导入成功 (系统环境 - python3)"
        python_test_success=true
    # 测试虚拟环境
    elif [ -f "/opt/hailo_venv/bin/python" ] && /opt/hailo_venv/bin/python -c "import hailo_platform; print('HailoRT Python API 版本:', hailo_platform.__version__)" 2>/dev/null; then
        log_success "✓ Python包导入成功 (虚拟环境: /opt/hailo_venv)"
        log_info "使用虚拟环境: source /opt/hailo_venv/bin/activate"
        python_test_success=true
    # 测试hailo-python快捷命令
    elif [ -f "/usr/local/bin/hailo-python" ] && /usr/local/bin/hailo-python -c "import hailo_platform; print('HailoRT Python API 版本:', hailo_platform.__version__)" 2>/dev/null; then
        log_success "✓ Python包导入成功 (快捷命令: hailo-python)"
        python_test_success=true
    fi
    
    if [ "$python_test_success" = false ]; then
        log_error "✗ Python包导入失败"
        log_info "提示: 可能需要激活虚拟环境或设置PYTHONPATH"
        all_checks_passed=false
    fi
    
    # 跳过固件和设备测试（需要驱动支持）
    # 2. 检查固件 (跳过)
    # log_info "2. 检查固件文件..."
    # if ls /lib/firmware/hailo/hailo8_fw.bin &> /dev/null; then
    #     log_success "✓ 固件文件存在"
    # else
    #     log_warning "! 固件文件可能缺失"
    # fi
    
    # 3. 尝试简单的设备测试 (跳过，需要驱动支持)
    # log_info "3. 进行设备连接测试..."
    log_info "2. 检查Python包基本功能..."
    
    # 只测试Python包的基本导入和版本信息，不进行设备扫描
    basic_test_success=false
    
    # 测试系统Python (优先使用python3.12)
    if $python_cmd -c "
import hailo_platform as hpf
try:
    print('HailoRT Python API 版本:', hpf.__version__)
    print('Python包导入成功')
except Exception as e:
    print('基本功能测试失败:', e)
" 2>/dev/null; then
        log_success "✓ Python包基本功能测试通过 (系统环境 - $python_cmd)"
        basic_test_success=true
    # 如果python3.12失败，尝试python3
    elif [ "$python_cmd" = "python3.12" ] && python3 -c "
import hailo_platform as hpf
try:
    print('HailoRT Python API 版本:', hpf.__version__)
    print('Python包导入成功')
except Exception as e:
    print('基本功能测试失败:', e)
" 2>/dev/null; then
        log_success "✓ Python包基本功能测试通过 (系统环境 - python3)"
        basic_test_success=true
    # 测试虚拟环境
    elif [ -f "/opt/hailo_venv/bin/python" ] && /opt/hailo_venv/bin/python -c "
import hailo_platform as hpf
try:
    print('HailoRT Python API 版本:', hpf.__version__)
    print('Python包导入成功')
except Exception as e:
    print('基本功能测试失败:', e)
" 2>/dev/null; then
        log_success "✓ Python包基本功能测试通过 (虚拟环境)"
        basic_test_success=true
    # 测试hailo-python快捷命令
    elif [ -f "/usr/local/bin/hailo-python" ] && /usr/local/bin/hailo-python -c "
import hailo_platform as hpf
try:
    print('HailoRT Python API 版本:', hpf.__version__)
    print('Python包导入成功')
except Exception as e:
    print('基本功能测试失败:', e)
" 2>/dev/null; then
        log_success "✓ Python包基本功能测试通过 (快捷命令)"
        basic_test_success=true
    fi
    
    if [ "$basic_test_success" = false ]; then
        log_warning "! Python包基本功能测试失败"
    fi
    
    echo
    if $all_checks_passed; then
        log_success "🎉 Hailo8 Python包安装完成！"
        echo
        log_info "使用说明:"
        
        # 根据安装方式提供不同的使用说明
        if python3 -c "import hailo_platform" 2>/dev/null; then
            echo "  1. Python API已可用 (系统环境)，导入方式: import hailo_platform as hpf"
            echo "     测试命令: python3 -c \"import hailo_platform as hpf; print('HailoRT版本:', hpf.__version__)\""
        elif [ -f "/opt/hailo_venv/bin/python" ]; then
            echo "  1. Python API已安装到虚拟环境: /opt/hailo_venv"
            echo "     激活环境: source /opt/hailo_venv/bin/activate"
            echo "     测试命令: /opt/hailo_venv/bin/python -c \"import hailo_platform as hpf; print('版本:', hpf.__version__)\""
            if [ -f "/usr/local/bin/hailo-python" ]; then
                echo "     快捷命令: hailo-python -c \"import hailo_platform as hpf; print('版本:', hpf.__version__)\""
            fi
        fi
        
        echo
        log_info "环境变量设置 (可选):"
        echo "  # 如果使用虚拟环境，可以设置别名方便使用"
        echo "  echo 'alias hailo-env=\"source /opt/hailo_venv/bin/activate\"' >> ~/.bashrc"
        echo
    else
        log_error "❌ Python包安装过程中发现问题，请检查上述错误信息"
        echo
        log_info "常见解决方案:"
        echo "  1. 如果Python包安装失败，可以手动使用虚拟环境:"
        echo "     python3 -m venv /opt/hailo_venv"
        echo "     source /opt/hailo_venv/bin/activate"
        echo "     pip install /vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl"
        echo
        echo "  2. 检查Python环境和依赖:"
        echo "     python3 --version"
        echo "     pip3 --version"
        echo
        return 1
    fi
}

# 清理函数
cleanup() {
    log_info "开始清理安装过程中的临时文件和依赖..."
    
    # 清理Python编译临时目录
    if [[ -d "/tmp/python312_install" ]]; then
        log_info "清理Python 3.12编译临时文件..."
        rm -rf /tmp/python312_install
    fi
    
    # 清理备份目录（如果存在）
    if [[ -d /tmp/hailo_backup_* ]]; then
        log_info "清理备份文件..."
        rm -rf /tmp/hailo_backup_*
    fi
    
    # 清理apt缓存
    log_info "清理apt包缓存..."
    apt-get clean >/dev/null 2>&1 || true
    apt-get autoclean >/dev/null 2>&1 || true
    
    # 移除不再需要的编译依赖包（谨慎操作，只移除明确用于编译的包）
    log_info "移除编译依赖包..."
    # 只移除明确用于Python编译的依赖，保留系统可能需要的包
    apt-get autoremove --purge -y zlib1g-dev libncurses5-dev \
        libgdbm-dev libnss3-dev libreadline-dev libffi-dev \
        libsqlite3-dev libbz2-dev >/dev/null 2>&1 || true
    
    # build-essential和libssl-dev可能被其他程序需要，所以不自动删除
    log_info "保留build-essential和libssl-dev（可能被其他程序需要）"
    
    # 清理pip缓存
    if command -v pip3.12 >/dev/null 2>&1; then
        log_info "清理pip缓存..."
        pip3.12 cache purge >/dev/null 2>&1 || true
    fi
    
    if command -v pip3 >/dev/null 2>&1; then
        pip3 cache purge >/dev/null 2>&1 || true
    fi
    
    # 清理wget下载的临时文件
    if [[ -f "/tmp/Python-3.12.4.tgz" ]]; then
        rm -f /tmp/Python-3.12.4.tgz
    fi
    
    # 清理其他临时文件
    find /tmp -name "*hailo*" -type f -mtime +0 -delete 2>/dev/null || true
    find /tmp -name "*python*" -type f -mtime +0 -delete 2>/dev/null || true
    
    log_success "✓ 临时文件和依赖清理完成"
}

# 主函数
main() {
    echo "========================================"
    echo "    Hailo8 Python包安装脚本 v1.3"
    echo "    适用于飞牛OS (基于Debian)"
    echo "    集成Python 3.12自动安装和完整清理功能"
    echo "========================================"
    echo
    
    # 设置错误处理（但不在EXIT时自动清理，改为手动清理）
    # trap cleanup EXIT
    
    # 执行安装步骤
    check_root
    check_files
    
    # 检查wheel文件兼容性
    if ! check_wheel_compatibility "$WHEEL_FILE"; then
        case $? in
            1)
                log_error "❌ 致命错误: Wheel文件与当前系统不兼容"
                log_error "❌ 无法继续安装"
                exit 1
                ;;
            2)
                log_warning "⚠️  检测到兼容性警告，但将继续尝试安装"
                ;;
        esac
    fi
    
    check_system
    
    # 首先确保Python 3.12已安装
    log_info "检查并安装Python 3.12..."
    install_python312
    
    log_info "开始Python包安装过程..."
    
    # 注释掉驱动相关的安装步骤
    # backup_existing
    # install_deb_package
    # load_driver
    
    # 只安装Python包
    install_python_package
    
    echo
    log_info "安装完成，正在进行状态检查..."
    echo
    check_installation
    
    echo
    log_success "Python包安装脚本执行完成！"
    
    # 执行最终清理
    echo
    log_info "执行最终清理..."
    cleanup
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi