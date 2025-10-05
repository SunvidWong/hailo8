# Hailo8 TPU 智能安装管理器 - 构建和部署指南

## 概述

本文档详细说明了如何构建、部署和使用 Hailo8 TPU 智能安装管理器。该系统具有容错能力、自动纠错功能，确保 100% 安装成功率，并支持 Docker 集成。

## 系统架构

```
Hailo8 安装管理器
├── install.sh              # 主安装脚本（入口点）
├── hailo8_installer.py     # 核心安装逻辑
├── docker_hailo8.py        # Docker 集成管理
├── test_hailo8.py          # 安装验证测试
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
└── De/                     # 安装包目录
    ├── *.deb               # Debian 包
    ├── *.whl               # Python 包
    └── *.rpm               # RPM 包（可选）
```

## 构建要求

### 系统要求
- **操作系统**: Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+
- **架构**: x86_64
- **内核**: Linux 4.15+
- **内存**: 至少 4GB RAM
- **存储**: 至少 2GB 可用空间
- **权限**: root 或 sudo 权限

### 软件依赖
- Python 3.7+
- pip3
- Git
- curl/wget
- 基础构建工具 (build-essential, cmake)

## 构建步骤

### 1. 环境准备

```bash
# 更新系统包
sudo apt-get update  # Ubuntu/Debian
# 或
sudo yum update       # CentOS/RHEL

# 安装基础依赖
sudo apt-get install -y python3 python3-pip git curl build-essential cmake
# 或
sudo yum install -y python3 python3-pip git curl gcc gcc-c++ make cmake
```

### 2. 获取源代码

```bash
# 克隆仓库
git clone <repository-url>
cd Linux-debain-intall-hailo8

# 或直接下载并解压
wget <archive-url>
tar -xzf hailo8-installer.tar.gz
cd hailo8-installer
```

### 3. 准备安装包

将 Hailo8 安装包放置到 `De/` 目录：

```bash
mkdir -p De/
# 复制以下文件到 De/ 目录：
# - hailort_*.deb
# - hailort-*-linux_x86_64.whl
# - hailort-pcie-driver_*.deb
```

### 4. 验证构建

```bash
# 检查文件完整性
ls -la De/
ls -la *.py *.sh *.yaml *.txt

# 验证 Python 脚本语法
python3 -m py_compile hailo8_installer.py
python3 -m py_compile docker_hailo8.py
python3 -m py_compile test_hailo8.py

# 检查脚本权限
chmod +x install.sh *.py
```

## 部署方式

### 方式一：直接部署（推荐）

```bash
# 1. 复制整个目录到目标系统
scp -r hailo8-installer/ user@target-host:/opt/

# 2. 在目标系统上运行
ssh user@target-host
cd /opt/hailo8-installer
sudo ./install.sh
```

### 方式二：打包部署

```bash
# 创建部署包
tar -czf hailo8-installer-$(date +%Y%m%d).tar.gz \
    install.sh \
    *.py \
    *.yaml \
    *.txt \
    *.md \
    De/

# 传输到目标系统
scp hailo8-installer-*.tar.gz user@target-host:/tmp/

# 在目标系统解压并安装
ssh user@target-host
cd /tmp
tar -xzf hailo8-installer-*.tar.gz
cd hailo8-installer
sudo ./install.sh
```

### 方式三：容器化部署

```bash
# 创建 Dockerfile
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl wget git \
    build-essential cmake pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hailo8-installer
COPY . .

RUN chmod +x install.sh *.py
RUN pip3 install -r requirements.txt

CMD ["./install.sh", "--help"]
EOF

# 构建镜像
docker build -t hailo8-installer:latest .

# 运行容器
docker run -it --privileged \
    -v /dev:/dev \
    -v /lib/modules:/lib/modules:ro \
    hailo8-installer:latest
```

## 使用方法

### 交互式安装

```bash
# 运行主安装脚本
sudo ./install.sh

# 选择安装模式：
# 1) 完整安装 (推荐)
# 2) 仅安装驱动和 HailoRT
# 3) 仅配置 Docker 集成
# 4) 运行系统测试
# 5) 修复现有安装
# 6) 卸载 Hailo8
# 7) 显示安装状态
# 8) 退出
```

### 命令行安装

```bash
# 完整安装
sudo ./install.sh --full-install

# 基础安装
sudo ./install.sh --basic-install

# 仅 Docker 集成
sudo ./install.sh --docker-only

# 运行测试
sudo ./install.sh --test-only

# 修复安装
sudo ./install.sh --repair

# 卸载
sudo ./install.sh --uninstall

# 查看状态
sudo ./install.sh --status
```

### 单独使用组件

```bash
# 使用核心安装器
sudo python3 hailo8_installer.py --full-install

# 使用 Docker 管理器
sudo python3 docker_hailo8.py --packages-dir ./De

# 运行测试
sudo python3 test_hailo8.py
```

## 配置选项

### 修改 config.yaml

```yaml
# 基础配置
basic:
  install_directory: "/opt/hailo"
  package_directory: "./De"
  max_retries: 3
  command_timeout: 300

# 系统检查
system_check:
  skip_check: false
  supported_distros: ["ubuntu", "debian", "centos", "rhel"]
  min_kernel_version: "4.15"
  min_disk_space_gb: 2

# Docker 配置
docker:
  enable: true
  auto_install: true
  image_name: "hailo8:latest"
  base_image: "ubuntu:22.04"

# 日志配置
logging:
  level: "INFO"
  retention_days: 30
  colored_output: true
```

## 故障排除

### 常见问题

1. **权限错误**
   ```bash
   # 确保以 root 权限运行
   sudo ./install.sh
   ```

2. **Python 依赖缺失**
   ```bash
   # 手动安装依赖
   pip3 install -r requirements.txt
   ```

3. **安装包缺失**
   ```bash
   # 检查 De/ 目录
   ls -la De/
   # 确保包含 .deb 和 .whl 文件
   ```

4. **Docker 权限问题**
   ```bash
   # 添加用户到 docker 组
   sudo usermod -aG docker $USER
   # 重新登录或运行
   newgrp docker
   ```

### 日志分析

```bash
# 查看安装日志
tail -f install.log

# 查看详细日志
tail -f hailo8_installer.log
tail -f docker_hailo8.log
tail -f hailo8_test.log

# 查看系统日志
journalctl -u docker
dmesg | grep hailo
```

### 手动修复

```bash
# 重新加载驱动
sudo modprobe -r hailo_pci
sudo modprobe hailo_pci

# 重启 Docker
sudo systemctl restart docker

# 检查设备节点
ls -la /dev/hailo*

# 检查 PCIe 设备
lspci -d 1e60:
```

## 性能优化

### 系统调优

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p
```

### Docker 优化

```bash
# 配置 Docker 存储驱动
cat > /etc/docker/daemon.json << 'EOF'
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

## 安全考虑

### 权限管理

```bash
# 创建专用用户
sudo useradd -r -s /bin/false hailo
sudo usermod -aG docker hailo

# 设置文件权限
sudo chown -R root:hailo /opt/hailo
sudo chmod -R 750 /opt/hailo
```

### 网络安全

```bash
# 配置防火墙（如果需要）
sudo ufw allow from 192.168.1.0/24 to any port 8888  # Jupyter
sudo ufw enable
```

## 监控和维护

### 健康检查

```bash
# 创建健康检查脚本
cat > /usr/local/bin/hailo8-health-check.sh << 'EOF'
#!/bin/bash
python3 /opt/hailo8-installer/test_hailo8.py --quick
EOF

chmod +x /usr/local/bin/hailo8-health-check.sh

# 添加到 crontab
echo "0 */6 * * * /usr/local/bin/hailo8-health-check.sh" | sudo crontab -
```

### 自动更新

```bash
# 创建更新脚本
cat > /usr/local/bin/hailo8-update.sh << 'EOF'
#!/bin/bash
cd /opt/hailo8-installer
git pull origin main
./install.sh --repair
EOF

chmod +x /usr/local/bin/hailo8-update.sh
```

## 支持和贡献

### 获取支持

1. 查看日志文件
2. 运行诊断测试
3. 检查系统兼容性
4. 提交 Issue 时包含完整日志

### 贡献代码

1. Fork 仓库
2. 创建功能分支
3. 提交 Pull Request
4. 确保通过所有测试

## 版本历史

- **v1.0.0**: 初始版本，支持基础安装和 Docker 集成
- **v1.1.0**: 添加容错和自动修复功能
- **v1.2.0**: 增强 Docker 支持和性能优化

---

**注意**: 本文档会随着软件更新而持续更新，请定期查看最新版本。