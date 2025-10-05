# Hailo8 Python包一键安装指南

本指南提供了在飞牛OS（基于Debian）系统上一键安装Hailo8 Python API的完整解决方案。

## 文件说明

- `install_hailo8_onekey.sh` - Python包一键安装脚本
- `hailort-4.23.0-cp312-cp312-linux_x86_64.whl` - HailoRT Python包文件
- `PYTHON_ENV_GUIDE.md` - Python环境管理详细指南

## 安装步骤

### 1. 准备工作

确保系统已安装基本依赖：
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. 运行安装脚本

```bash
# 赋予执行权限
chmod +x install_hailo8_onekey.sh

# 运行安装脚本
sudo ./install_hailo8_onekey.sh
```

### 3. 安装后验证

脚本会自动进行以下验证：
- Python包导入测试
- 版本信息检查
- 基本功能测试

## 使用方法

### 系统环境安装
如果Python包成功安装到系统环境：
```python
import hailo_platform as hpf
print('HailoRT版本:', hpf.__version__)
```

### 虚拟环境安装
如果安装到虚拟环境（`/opt/hailo_venv`）：
```bash
# 激活虚拟环境
source /opt/hailo_venv/bin/activate

# 使用Python API
python -c "import hailo_platform as hpf; print('版本:', hpf.__version__)"

# 或使用快捷命令（如果可用）
hailo-python -c "import hailo_platform as hpf; print('版本:', hpf.__version__)"
```

## 故障排除

### 1. "externally-managed-environment" 错误
这是现代Linux发行版的安全特性。脚本会自动尝试以下解决方案：
1. 使用 `--break-system-packages` 标志
2. 用户级安装 `--user`
3. 创建虚拟环境安装

### 2. Python包导入失败
```bash
# 检查Python环境
python3 --version
pip3 --version

# 手动安装到虚拟环境
python3 -m venv /opt/hailo_venv
source /opt/hailo_venv/bin/activate
pip install /vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl
```

### 3. 权限问题
确保以root权限运行脚本：
```bash
sudo ./install_hailo8_onekey.sh
```

## 脚本特性

- **智能安装策略**: 自动尝试多种Python包安装方法
- **环境兼容性**: 支持系统环境和虚拟环境
- **全面检查**: 安装后自动验证功能
- **错误恢复**: 提供详细的故障排除指导
- **日志记录**: 详细的安装过程日志

## 支持的系统

- 飞牛OS (基于Debian)
- Ubuntu 20.04+
- Debian 11+
- 其他基于Debian的发行版

## 注意事项

1. **Python版本**: 需要Python 3.8+
2. **网络连接**: 安装依赖时需要网络连接
3. **存储空间**: 确保有足够的磁盘空间
4. **权限要求**: 需要sudo权限进行系统级安装

## 环境变量设置（可选）

如果使用虚拟环境，可以设置别名方便使用：
```bash
echo 'alias hailo-env="source /opt/hailo_venv/bin/activate"' >> ~/.bashrc
source ~/.bashrc
```

## 技术支持

如遇到问题，请提供以下信息：
- 系统版本：`cat /etc/os-release`
- Python版本：`python3 --version`
- 错误日志：脚本运行时的完整输出
- 安装文件：确认wheel文件路径和权限

更多详细信息请参考 `PYTHON_ENV_GUIDE.md`。