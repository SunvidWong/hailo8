# Hailo8 TPU 智能安装管理器

一个具有完整容错、纠错和回滚能力的 Hailo8 TPU 安装管理软件，确保 100% 安装成功，支持 Docker 集成。

## 🚀 主要特性

- **智能容错**: 自动检测和处理安装过程中的各种错误
- **自动纠错**: 内置多种修复策略，自动解决常见问题
- **完整回滚**: 支持完整的安装回滚，确保系统安全
- **状态管理**: 实时保存安装状态，支持断点续装
- **Docker 集成**: 自动配置 Docker 以支持 Hailo8 设备访问
- **多平台支持**: 支持 Ubuntu、Debian、CentOS、RHEL、Fedora
- **详细日志**: 完整的安装日志记录，便于问题诊断

## 📋 系统要求

- **操作系统**: Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+, RHEL 7+, Fedora 30+)
- **内核版本**: 4.0+
- **权限**: root 权限
- **磁盘空间**: 至少 2GB 可用空间
- **Python**: Python 3.6+

## 📦 安装包要求

请确保 `De/` 目录下包含以下文件：
- `hailort-pcie-driver_4.23.0_all.deb` - PCIe 驱动包
- `hailort_4.23.0_amd64.deb` - HailoRT 运行时包
- `hailort-4.23.0-cp313-cp313-linux_x86_64.whl` - Python 包

## 🛠️ 安装步骤

### 1. 准备环境

```bash
# 确保以 root 权限运行
sudo su

# 安装 Python 依赖
pip3 install -r requirements.txt

# 给安装程序执行权限
chmod +x hailo8_installer.py
```

### 2. 执行安装

```bash
# 完整安装
python3 hailo8_installer.py

# 查看安装状态
python3 hailo8_installer.py --status

# 回滚安装
python3 hailo8_installer.py --rollback
```

## 📊 安装组件

安装程序包含以下组件：

1. **系统环境检查** ⏳
   - Linux 发行版兼容性检查
   - 内核版本验证
   - 硬件兼容性检测
   - 权限和磁盘空间检查

2. **系统依赖安装** ⏳
   - 自动检测包管理器 (apt/yum/dnf)
   - 安装编译工具链
   - 安装 Python 开发环境
   - 安装内核头文件

3. **PCIe 驱动安装** ⏳
   - 安装 Hailo PCIe 驱动包
   - 加载驱动模块
   - 验证设备节点创建

4. **HailoRT 运行时安装** ⏳
   - 安装 HailoRT DEB 包
   - 安装 Python 绑定
   - 验证 CLI 工具和 Python 模块

5. **Docker 配置** ⏳
   - 安装 Docker (如果未安装)
   - 配置设备访问权限
   - 创建测试镜像

6. **安装验证** ⏳
   - 驱动功能测试
   - HailoRT 功能测试
   - Docker 集成测试
   - 设备访问测试

## 🔧 高级功能

### 状态管理

安装程序会自动保存安装状态到 `/opt/hailo8/install_state.json`，支持：
- 断点续装
- 状态查询
- 错误诊断

### 容错机制

- **重试机制**: 每个组件最多重试 3 次
- **自动修复**: 内置多种修复策略
- **依赖修复**: 自动修复包依赖问题
- **驱动重建**: 自动重建损坏的驱动

### 回滚功能

```bash
# 完整回滚安装
python3 hailo8_installer.py --rollback
```

回滚操作包括：
- 卸载驱动模块
- 移除软件包
- 清理配置文件
- 恢复系统状态

## 📁 目录结构

```
/opt/hailo8/
├── logs/                    # 安装日志
├── backup/                  # 系统状态备份
├── install_state.json       # 安装状态文件
└── ...
```

## 🐳 Docker 使用

安装完成后，可以在 Docker 中使用 Hailo8：

```bash
# 运行测试容器
docker run --rm --device=/dev/hailo0 hailo8:latest

# 在容器中使用 Hailo8
docker run -it --device=/dev/hailo0 hailo8:latest python3 -c "
import hailo_platform
print('Hailo8 在 Docker 中运行正常')
"
```

## 🔍 故障排除

### 常见问题

1. **权限不足**
   ```bash
   sudo python3 hailo8_installer.py
   ```

2. **包依赖问题**
   ```bash
   apt --fix-broken install -y
   dpkg --configure -a
   ```

3. **驱动加载失败**
   ```bash
   modprobe hailo_pci
   dmesg | grep hailo
   ```

4. **设备节点不存在**
   ```bash
   ls -la /dev/hailo*
   lspci -d 1e60:
   ```

### 日志查看

```bash
# 查看最新日志
tail -f /opt/hailo8/logs/hailo8_install_*.log

# 查看系统日志
dmesg | grep hailo
journalctl -u docker
```

## 🤝 技术支持

如果遇到问题，请提供以下信息：
1. 操作系统版本: `cat /etc/os-release`
2. 内核版本: `uname -r`
3. 安装日志: `/opt/hailo8/logs/`
4. 系统日志: `dmesg | grep hailo`

## 📄 许可证

本软件遵循 MIT 许可证。

## 🔄 更新日志

### v1.0.0
- 初始版本发布
- 支持完整的 Hailo8 安装流程
- 实现容错和回滚机制
- 添加 Docker 集成支持