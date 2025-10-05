# Hailo8 PCIe驱动编译项目

本项目包含了为飞牛OS编译Hailo8 PCIe驱动的完整解决方案。

## 项目结构

```
hailo8/
├── hailort-drivers-master/          # Hailo驱动源码
├── compile_instructions.md          # 详细编译指导文档
├── compile_hailo8_driver.sh         # Linux环境自动编译脚本
├── docker_compile.sh               # macOS Docker编译脚本
└── README.md                       # 本文档
```

## 快速开始

### 方案1: 在macOS上使用Docker编译（推荐）

如果你在macOS环境下，可以使用Docker来编译Linux驱动：

```bash
# 确保Docker Desktop已安装并运行
./docker_compile.sh
```

### 方案2: 在Linux环境中直接编译

如果你有Linux环境（虚拟机、服务器或飞牛OS设备）：

```bash
# 自动安装依赖并编译
./compile_hailo8_driver.sh

# 仅编译不安装
./compile_hailo8_driver.sh --compile-only

# 跳过依赖安装
./compile_hailo8_driver.sh --no-deps
```

### 方案3: 手动编译

参考 `compile_instructions.md` 文档进行手动编译。

## 编译环境要求

- **Linux内核**: 支持的Linux发行版（Ubuntu、CentOS、Debian等）
- **编译工具**: build-essential, make, gcc
- **内核头文件**: linux-headers-$(uname -r)
- **可选**: dkms（用于动态内核模块支持）

## 支持的系统

- Ubuntu 18.04+
- CentOS 7+
- Debian 9+
- Red Hat Enterprise Linux 7+
- Rocky Linux 8+
- Fedora 30+
- 飞牛OS（基于Linux）

## 编译输出

成功编译后会生成：
- `hailo1x_pci.ko` - 主驱动模块文件

## 安装和使用

### 在目标系统上安装驱动

```bash
# 复制驱动文件到系统目录
sudo cp hailo1x_pci.ko /lib/modules/$(uname -r)/kernel/drivers/misc/

# 更新模块依赖
sudo depmod -a

# 加载驱动
sudo modprobe hailo1x_pci

# 验证驱动加载
lsmod | grep hailo
ls -la /dev/hailo*
```

### 设置开机自动加载

```bash
# 添加到模块加载列表
echo "hailo1x_pci" | sudo tee -a /etc/modules

# 或者创建配置文件
sudo cp hailort-drivers-master/linux/pcie/hailo1x_pci.conf /etc/modprobe.d/
```

## 故障排除

### 编译错误

1. **内核头文件缺失**
   ```bash
   # Ubuntu/Debian
   sudo apt install linux-headers-$(uname -r)
   
   # CentOS/RHEL
   sudo yum install kernel-devel-$(uname -r)
   ```

2. **编译工具缺失**
   ```bash
   # Ubuntu/Debian
   sudo apt install build-essential
   
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   ```

3. **权限问题**
   - 编译时不需要root权限
   - 安装时需要sudo权限

### 运行时错误

1. **驱动加载失败**
   ```bash
   # 检查内核日志
   dmesg | grep hailo
   
   # 检查模块信息
   modinfo hailo1x_pci
   ```

2. **设备节点未创建**
   - 确保Hailo设备已正确连接
   - 检查udev规则是否正确安装

## 飞牛OS特殊说明

飞牛OS基于Linux内核，但可能有特定的配置要求：

1. **内核版本兼容性**: 确保编译环境的内核版本与飞牛OS匹配
2. **自定义内核**: 飞牛OS可能使用自定义内核配置
3. **安全模块**: 可能需要禁用Secure Boot或配置内核模块签名

### 获取飞牛OS内核信息

```bash
# 在飞牛OS设备上运行
uname -r                    # 内核版本
cat /proc/version          # 详细内核信息
lsmod | head -10           # 已加载模块
```

## 技术支持

- **Hailo官方文档**: <mcreference link="https://github.com/hailo-ai/hailort-drivers/tree/master/linux/pcie" index="0">0</mcreference>
- **驱动源码**: https://github.com/hailo-ai/hailort-drivers
- **问题反馈**: 请在GitHub仓库提交Issue

## 许可证

本项目遵循Hailo官方驱动的许可证条款（GPL-2.0）。

## 更新日志

- **v1.0**: 初始版本，支持基本编译功能
- **v1.1**: 添加Docker编译支持
- **v1.2**: 增加自动化脚本和详细文档

---

**注意**: 请确保在兼容的内核版本上使用编译的驱动，不匹配的内核版本可能导致系统不稳定。