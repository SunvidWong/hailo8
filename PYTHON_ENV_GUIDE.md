# Hailo8 Python环境使用指南

## 问题说明

在现代Linux发行版（如飞牛OS、Ubuntu 22.04+、Debian 12+）中，Python环境被设置为"外部管理"，这意味着不能直接使用 `pip` 安装包到系统Python环境中。这是为了防止系统包管理器和pip之间的冲突。

## 错误信息
```
error: externally-managed-environment
× This environment is externally managed
```

## 解决方案

我们的一键安装脚本已经自动处理了这个问题，提供了三种安装方式：

### 方案1: 系统级安装 (推荐用于驱动)
```bash
pip3 install package.whl --break-system-packages
```
- ✅ **优点**: 全局可用，无需激活环境
- ⚠️ **注意**: 绕过系统保护，仅用于必要的系统级驱动

### 方案2: 用户级安装
```bash
pip3 install package.whl --user
```
- ✅ **优点**: 不影响系统环境
- ⚠️ **注意**: 可能需要设置PATH

### 方案3: 虚拟环境安装 (最安全)
```bash
python3 -m venv /opt/hailo_venv
source /opt/hailo_venv/bin/activate
pip install package.whl
```
- ✅ **优点**: 完全隔离，最安全
- ⚠️ **注意**: 需要激活环境才能使用

## 使用方法

### 如果安装到系统环境
```bash
# 直接使用
python3 -c "import hailo_platform as hpf; print(hpf.__version__)"
```

### 如果安装到虚拟环境
```bash
# 方法1: 激活虚拟环境
source /opt/hailo_venv/bin/activate
python -c "import hailo_platform as hpf; print(hpf.__version__)"
deactivate  # 退出虚拟环境

# 方法2: 直接使用虚拟环境的Python
/opt/hailo_venv/bin/python -c "import hailo_platform as hpf; print(hpf.__version__)"

# 方法3: 使用快捷命令 (如果脚本创建了)
hailo-python -c "import hailo_platform as hpf; print(hpf.__version__)"
```

### 设置便捷别名
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'alias hailo-env="source /opt/hailo_venv/bin/activate"' >> ~/.bashrc
echo 'alias hailo-python="/opt/hailo_venv/bin/python"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc

# 使用别名
hailo-env  # 激活环境
hailo-python -c "import hailo_platform"  # 直接运行
```

## 开发环境设置

### 在IDE中使用虚拟环境

#### VS Code
1. 打开命令面板 (Ctrl+Shift+P)
2. 选择 "Python: Select Interpreter"
3. 选择 `/opt/hailo_venv/bin/python`

#### PyCharm
1. File → Settings → Project → Python Interpreter
2. 添加新解释器 → Existing Environment
3. 选择 `/opt/hailo_venv/bin/python`

### Jupyter Notebook
```bash
# 在虚拟环境中安装jupyter
source /opt/hailo_venv/bin/activate
pip install jupyter ipykernel

# 注册内核
python -m ipykernel install --user --name=hailo_env --display-name="Hailo Environment"

# 启动jupyter
jupyter notebook
```

## 脚本开发

### 在脚本中使用虚拟环境
```bash
#!/bin/bash
# 方法1: 在脚本中激活虚拟环境
source /opt/hailo_venv/bin/activate
python your_script.py
deactivate
```

```python
#!/opt/hailo_venv/bin/python
# 方法2: 直接使用虚拟环境的Python作为shebang
import hailo_platform as hpf
# 你的代码...
```

### Python脚本模板
```python
#!/usr/bin/env python3
"""
Hailo8 应用示例
确保在正确的Python环境中运行此脚本
"""

import sys
import os

def check_hailo_environment():
    """检查Hailo环境是否可用"""
    try:
        import hailo_platform as hpf
        print(f"✓ HailoRT版本: {hpf.__version__}")
        
        # 扫描设备
        devices = hpf.scan_devices()
        print(f"✓ 找到设备: {len(devices)}个")
        
        return True
    except ImportError as e:
        print(f"✗ 无法导入hailo_platform: {e}")
        print("请确保:")
        print("1. 已安装HailoRT Python包")
        print("2. 在正确的Python环境中运行")
        print("3. 如使用虚拟环境，请先激活: source /opt/hailo_venv/bin/activate")
        return False
    except Exception as e:
        print(f"✗ 环境检查失败: {e}")
        return False

if __name__ == "__main__":
    if check_hailo_environment():
        print("🎉 Hailo环境检查通过，可以开始开发!")
        # 你的应用代码...
    else:
        sys.exit(1)
```

## 故障排除

### 问题1: 找不到hailo_platform模块
```bash
# 检查当前Python环境
which python3
python3 -c "import sys; print(sys.path)"

# 检查是否在虚拟环境中
echo $VIRTUAL_ENV

# 如果使用虚拟环境，确保已激活
source /opt/hailo_venv/bin/activate
```

### 问题2: 权限问题
```bash
# 检查虚拟环境权限
ls -la /opt/hailo_venv/

# 如果权限不正确，修复权限
sudo chown -R $USER:$USER /opt/hailo_venv/
```

### 问题3: 包版本冲突
```bash
# 在虚拟环境中检查已安装的包
source /opt/hailo_venv/bin/activate
pip list | grep hailo

# 重新安装
pip uninstall hailort
pip install /vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl
```

## 最佳实践

1. **生产环境**: 使用虚拟环境，确保环境隔离
2. **开发环境**: 使用虚拟环境，便于管理依赖
3. **系统服务**: 可以考虑系统级安装，但要谨慎
4. **多项目**: 为每个项目创建独立的虚拟环境

## 环境管理工具

### 使用conda (可选)
```bash
# 安装miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建hailo环境
conda create -n hailo python=3.12
conda activate hailo
pip install /vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl
```

### 使用pipenv (可选)
```bash
# 安装pipenv
pip3 install --user pipenv

# 创建项目环境
mkdir hailo_project && cd hailo_project
pipenv install /vol1/1000/hailo8/hailort-4.23.0-cp312-cp312-linux_x86_64.whl

# 使用环境
pipenv shell
```

---

**注意**: 这个指南适用于飞牛OS和其他现代Linux发行版。选择最适合你使用场景的方案。