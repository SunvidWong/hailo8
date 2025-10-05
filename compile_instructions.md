# Hailo8驱动编译指南

## 系统要求

Hailo8 PCIe驱动需要在Linux系统上编译，不支持macOS/Darwin系统。

## 编译环境准备

### 方案1：使用Docker容器（推荐）

1. 安装Docker Desktop for Mac
2. 创建Linux编译环境：

```bash
# 拉取Ubuntu镜像
docker pull ubuntu:22.04

# 启动容器并挂载源码目录
docker run -it -v $(pwd):/workspace ubuntu:22.04 bash

# 在容器内安装编译依赖
apt update
apt install -y build-essential linux-headers-generic make gcc
```

### 方案2：使用虚拟机

1. 安装VMware Fusion或VirtualBox
2. 创建Ubuntu/CentOS虚拟机
3. 在虚拟机中安装编译环境

### 方案3：使用飞牛OS目标机器

直接在飞牛OS系统上编译（最佳方案）

## 编译步骤

在Linux环境中执行以下步骤：

### 1. 安装编译依赖

**Ubuntu/Debian系统：**
```bash
sudo apt update
sudo apt install -y build-essential linux-headers-$(uname -r) make gcc
```

**CentOS/RHEL系统：**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install kernel-devel-$(uname -r) make gcc
```

### 2. 编译驱动

```bash
cd hailort-drivers-master/linux/pcie
make all
```

### 3. 安装驱动

```bash
sudo make install
```

### 4. 加载驱动

```bash
sudo modprobe hailo1x_pci
```

## 交叉编译（高级选项）

如果需要为特定内核版本交叉编译：

```bash
# 设置目标内核目录
export KERNEL_DIR=/path/to/target/kernel/headers
make all
```

## 验证安装

```bash
# 检查驱动是否加载
lsmod | grep hailo

# 检查设备节点
ls -la /dev/hailo*
```

## 注意事项

1. 驱动版本必须与目标系统内核版本兼容
2. 确保目标系统已安装对应的内核头文件
3. 编译环境的内核版本应与目标系统匹配
4. 飞牛OS可能需要特定的内核配置或补丁

## 故障排除

如果编译失败，检查：
- 内核头文件是否正确安装
- 编译工具链是否完整
- 内核版本是否支持
- 是否有权限问题

## 飞牛OS特殊说明

飞牛OS基于Linux，但可能有自定义内核配置。建议：
1. 确认飞牛OS的内核版本和配置
2. 检查是否需要特殊的编译参数
3. 联系飞牛OS官方获取驱动编译指导