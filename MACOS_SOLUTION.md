# macOS平台Hailo8安装解决方案

## 问题说明
当前的`hailort-4.23.0-cp312-cp312-linux_x86_64.whl`文件是为Linux x86_64平台编译的，无法在macOS ARM64系统上运行。

## 解决方案

### 方案1：使用Docker容器（推荐）
```bash
# 1. 安装Docker Desktop for Mac
# 2. 创建Linux容器环境
docker run -it --platform linux/x86_64 ubuntu:22.04 bash

# 3. 在容器内安装依赖
apt update && apt install -y python3.12 python3.12-pip wget

# 4. 复制wheel文件到容器
docker cp hailort-4.23.0-cp312-cp312-linux_x86_64.whl container_name:/tmp/

# 5. 在容器内安装
python3.12 -m pip install /tmp/hailort-4.23.0-cp312-cp312-linux_x86_64.whl
```

### 方案2：使用虚拟机
1. 安装VMware Fusion或Parallels Desktop
2. 创建Linux虚拟机（Ubuntu 22.04 x86_64）
3. 在虚拟机内运行安装脚本

### 方案3：远程Linux服务器
如果您有访问Linux服务器的权限：
1. 将文件上传到Linux服务器
2. 在服务器上运行安装脚本
3. 通过SSH远程使用

### 方案4：寻找macOS兼容版本
```bash
# 检查是否有macOS版本的HailoRT
pip3.12 search hailort
# 或访问官方网站查找macOS版本
```

## 当前系统信息
- 操作系统: macOS (Darwin)
- 架构: ARM64 (Apple Silicon)
- Python版本: 3.12.3
- 不兼容的wheel: linux_x86_64

## 建议
最推荐使用Docker方案，因为：
1. 不需要额外的硬件
2. 可以完全模拟Linux环境
3. 安装简单，资源占用相对较少
4. 可以保持与目标Linux环境的一致性