#!/usr/bin/env python3
"""
Hailo8 Docker 集成管理器
专门处理 Hailo8 TPU 的 Docker 配置、镜像构建和容器管理
"""

import os
import sys
import json
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class DockerHailo8Manager:
    """Hailo8 Docker 管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.setup_logging()
        self.config = self.load_config(config_file)
        self.docker_available = self.check_docker_availability()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('docker_hailo8.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            import yaml
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except ImportError:
            self.logger.warning("PyYAML 未安装，使用默认配置")
        except Exception as e:
            self.logger.warning(f"配置文件加载失败: {e}，使用默认配置")
        
        # 默认配置
        return {
            'docker': {
                'image_name': 'hailo8:latest',
                'base_image': 'ubuntu:22.04',
                'enable_gpu': False,
                'daemon_config': {
                    'default-runtime': 'runc',
                    'runtimes': {
                        'hailo': {
                            'path': '/usr/bin/runc'
                        }
                    }
                }
            },
            'hailo': {
                'device_nodes': ['/dev/hailo0', '/dev/hailo_pci'],
                'driver_module': 'hailo_pci'
            }
        }
    
    def run_command(self, command: List[str], timeout: int = 300) -> Tuple[bool, str, str]:
        """执行命令"""
        try:
            self.logger.debug(f"执行命令: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)
    
    def check_docker_availability(self) -> bool:
        """检查 Docker 是否可用"""
        success, _, _ = self.run_command(['which', 'docker'])
        if not success:
            self.logger.error("Docker 未安装")
            return False
        
        success, stdout, _ = self.run_command(['docker', 'version'])
        if not success:
            self.logger.error("Docker 服务未运行")
            return False
        
        self.logger.info("Docker 可用")
        return True
    
    def install_docker(self) -> bool:
        """安装 Docker"""
        if self.docker_available:
            self.logger.info("Docker 已安装")
            return True
        
        self.logger.info("开始安装 Docker...")
        
        try:
            # 检测系统类型
            success, stdout, _ = self.run_command(['lsb_release', '-si'])
            if success:
                distro = stdout.strip().lower()
            else:
                # 备用检测方法
                if os.path.exists('/etc/debian_version'):
                    distro = 'debian'
                elif os.path.exists('/etc/redhat-release'):
                    distro = 'redhat'
                else:
                    distro = 'unknown'
            
            if 'ubuntu' in distro or 'debian' in distro:
                return self._install_docker_debian()
            elif 'centos' in distro or 'rhel' in distro or 'redhat' in distro:
                return self._install_docker_rhel()
            else:
                self.logger.error(f"不支持的系统类型: {distro}")
                return False
                
        except Exception as e:
            self.logger.error(f"Docker 安装失败: {e}")
            return False
    
    def _install_docker_debian(self) -> bool:
        """在 Debian/Ubuntu 系统上安装 Docker"""
        commands = [
            # 更新包索引
            ['apt-get', 'update'],
            # 安装依赖
            ['apt-get', 'install', '-y', 'ca-certificates', 'curl', 'gnupg', 'lsb-release'],
            # 添加 Docker GPG 密钥
            ['mkdir', '-p', '/etc/apt/keyrings'],
            ['curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '-o', '/etc/apt/keyrings/docker.asc'],
            ['chmod', 'a+r', '/etc/apt/keyrings/docker.asc'],
            # 更新包索引
            ['apt-get', 'update'],
            # 安装 Docker
            ['apt-get', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-buildx-plugin', 'docker-compose-plugin']
        ]
        
        for cmd in commands:
            success, stdout, stderr = self.run_command(cmd)
            if not success:
                self.logger.error(f"命令失败: {' '.join(cmd)}")
                self.logger.error(f"错误: {stderr}")
                return False
        
        # 启动 Docker 服务
        success, _, _ = self.run_command(['systemctl', 'start', 'docker'])
        if not success:
            self.logger.error("Docker 服务启动失败")
            return False
        
        # 设置开机自启
        self.run_command(['systemctl', 'enable', 'docker'])
        
        self.docker_available = True
        self.logger.info("Docker 安装成功")
        return True
    
    def _install_docker_rhel(self) -> bool:
        """在 RHEL/CentOS 系统上安装 Docker"""
        commands = [
            # 安装依赖
            ['yum', 'install', '-y', 'yum-utils'],
            # 添加 Docker 仓库
            ['yum-config-manager', '--add-repo', 'https://download.docker.com/linux/centos/docker-ce.repo'],
            # 安装 Docker
            ['yum', 'install', '-y', 'docker-ce', 'docker-ce-cli', 'containerd.io', 'docker-buildx-plugin', 'docker-compose-plugin']
        ]
        
        for cmd in commands:
            success, stdout, stderr = self.run_command(cmd)
            if not success:
                self.logger.error(f"命令失败: {' '.join(cmd)}")
                self.logger.error(f"错误: {stderr}")
                return False
        
        # 启动 Docker 服务
        success, _, _ = self.run_command(['systemctl', 'start', 'docker'])
        if not success:
            self.logger.error("Docker 服务启动失败")
            return False
        
        # 设置开机自启
        self.run_command(['systemctl', 'enable', 'docker'])
        
        self.docker_available = True
        self.logger.info("Docker 安装成功")
        return True
    
    def configure_docker_daemon(self) -> bool:
        """配置 Docker 守护进程"""
        if not self.docker_available:
            self.logger.error("Docker 不可用")
            return False
        
        self.logger.info("配置 Docker 守护进程...")
        
        try:
            daemon_config_path = "/etc/docker/daemon.json"
            
            # 备份现有配置
            if os.path.exists(daemon_config_path):
                shutil.copy2(daemon_config_path, f"{daemon_config_path}.backup")
                self.logger.info("已备份现有 Docker 配置")
            
            # 创建目录
            os.makedirs("/etc/docker", exist_ok=True)
            
            # 准备配置
            daemon_config = self.config.get('docker', {}).get('daemon_config', {})
            
            # 添加 Hailo 设备支持
            if 'runtimes' not in daemon_config:
                daemon_config['runtimes'] = {}
            
            # 写入配置
            with open(daemon_config_path, 'w') as f:
                json.dump(daemon_config, f, indent=2)
            
            self.logger.info(f"Docker 配置已写入: {daemon_config_path}")
            
            # 重启 Docker 服务
            success, _, stderr = self.run_command(['systemctl', 'restart', 'docker'])
            if not success:
                self.logger.error(f"Docker 服务重启失败: {stderr}")
                return False
            
            self.logger.info("Docker 守护进程配置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"Docker 守护进程配置失败: {e}")
            return False
    
    def create_dockerfile(self, dockerfile_path: str) -> bool:
        """创建 Hailo8 Dockerfile"""
        try:
            base_image = self.config.get('docker', {}).get('base_image', 'ubuntu:22.04')
            
            dockerfile_content = f'''# Hailo8 TPU Docker 镜像
FROM {base_image}

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    python3-dev \\
    build-essential \\
    cmake \\
    pkg-config \\
    libusb-1.0-0-dev \\
    libudev-dev \\
    wget \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /opt/hailo

# 复制 Hailo 安装包
COPY packages/ ./packages/

# 安装 HailoRT
RUN if [ -f packages/hailort_*.deb ]; then \\
        dpkg -i packages/hailort_*.deb || apt-get install -f -y; \\
    fi

# 安装 Python 包
RUN if [ -f packages/hailort-*-py3-none-any.whl ]; then \\
        pip3 install packages/hailort-*-py3-none-any.whl; \\
    elif [ -f packages/hailort-*-linux_x86_64.whl ]; then \\
        pip3 install packages/hailort-*-linux_x86_64.whl; \\
    fi

# 安装其他 Python 依赖
RUN pip3 install numpy opencv-python pillow

# 创建测试脚本
RUN echo '#!/usr/bin/env python3' > /opt/hailo/test.py && \\
    echo 'import hailo_platform' >> /opt/hailo/test.py && \\
    echo 'devices = hailo_platform.Device.scan()' >> /opt/hailo/test.py && \\
    echo 'print(f"Found {{len(devices)}} Hailo devices")' >> /opt/hailo/test.py && \\
    echo 'for i, device in enumerate(devices):' >> /opt/hailo/test.py && \\
    echo '    print(f"Device {{i}}: {{device}}")' >> /opt/hailo/test.py && \\
    chmod +x /opt/hailo/test.py

# 设置入口点
CMD ["/bin/bash"]

# 添加标签
LABEL maintainer="Hailo8 Installer"
LABEL description="Hailo8 TPU Docker Image"
LABEL version="1.0"
'''
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            self.logger.info(f"Dockerfile 已创建: {dockerfile_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Dockerfile 创建失败: {e}")
            return False
    
    def build_hailo8_image(self, packages_dir: str) -> bool:
        """构建 Hailo8 Docker 镜像"""
        if not self.docker_available:
            self.logger.error("Docker 不可用")
            return False
        
        self.logger.info("开始构建 Hailo8 Docker 镜像...")
        
        try:
            # 创建临时构建目录
            with tempfile.TemporaryDirectory() as build_dir:
                dockerfile_path = os.path.join(build_dir, "Dockerfile")
                packages_build_dir = os.path.join(build_dir, "packages")
                
                # 创建 Dockerfile
                if not self.create_dockerfile(dockerfile_path):
                    return False
                
                # 复制安装包
                if os.path.exists(packages_dir):
                    shutil.copytree(packages_dir, packages_build_dir)
                    self.logger.info(f"已复制安装包到构建目录")
                else:
                    # 创建空的 packages 目录
                    os.makedirs(packages_build_dir)
                    self.logger.warning("安装包目录不存在，创建空目录")
                
                # 构建镜像
                image_name = self.config.get('docker', {}).get('image_name', 'hailo8:latest')
                
                success, stdout, stderr = self.run_command([
                    'docker', 'build', 
                    '-t', image_name,
                    '-f', dockerfile_path,
                    build_dir
                ], timeout=1800)  # 30分钟超时
                
                if success:
                    self.logger.info(f"Docker 镜像构建成功: {image_name}")
                    self.logger.debug(f"构建输出: {stdout}")
                    return True
                else:
                    self.logger.error(f"Docker 镜像构建失败: {stderr}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Docker 镜像构建异常: {e}")
            return False
    
    def test_hailo8_container(self) -> bool:
        """测试 Hailo8 容器"""
        if not self.docker_available:
            self.logger.error("Docker 不可用")
            return False
        
        self.logger.info("测试 Hailo8 容器...")
        
        try:
            image_name = self.config.get('docker', {}).get('image_name', 'hailo8:latest')
            device_nodes = self.config.get('hailo', {}).get('device_nodes', ['/dev/hailo0'])
            
            # 构建设备映射参数
            device_args = []
            for device in device_nodes:
                if os.path.exists(device):
                    device_args.extend(['--device', device])
                    self.logger.info(f"映射设备: {device}")
            
            if not device_args:
                self.logger.warning("未找到 Hailo 设备节点，跳过设备映射")
            
            # 运行测试容器
            cmd = [
                'docker', 'run', '--rm'
            ] + device_args + [
                image_name,
                'python3', '/opt/hailo/test.py'
            ]
            
            success, stdout, stderr = self.run_command(cmd, timeout=120)
            
            if success:
                self.logger.info("容器测试成功:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
                return True
            else:
                self.logger.error(f"容器测试失败: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"容器测试异常: {e}")
            return False
    
    def create_docker_compose(self, compose_path: str = "docker-compose.yml") -> bool:
        """创建 Docker Compose 文件"""
        try:
            image_name = self.config.get('docker', {}).get('image_name', 'hailo8:latest')
            device_nodes = self.config.get('hailo', {}).get('device_nodes', ['/dev/hailo0'])
            
            compose_content = f'''version: '3.8'

services:
  hailo8:
    image: {image_name}
    container_name: hailo8-container
    restart: unless-stopped
    devices:
'''
            
            # 添加设备映射
            for device in device_nodes:
                compose_content += f'      - "{device}:{device}"\n'
            
            compose_content += '''    volumes:
      - ./data:/opt/hailo/data
      - ./models:/opt/hailo/models
    environment:
      - PYTHONUNBUFFERED=1
    working_dir: /opt/hailo
    command: tail -f /dev/null
    
  hailo8-jupyter:
    image: {image_name}
    container_name: hailo8-jupyter
    restart: unless-stopped
    ports:
      - "8888:8888"
    devices:
'''.format(image_name=image_name)
            
            # 为 Jupyter 服务也添加设备映射
            for device in device_nodes:
                compose_content += f'      - "{device}:{device}"\n'
            
            compose_content += '''    volumes:
      - ./notebooks:/opt/hailo/notebooks
      - ./data:/opt/hailo/data
      - ./models:/opt/hailo/models
    environment:
      - PYTHONUNBUFFERED=1
    working_dir: /opt/hailo/notebooks
    command: >
      bash -c "pip3 install jupyter &&
               jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''"

volumes:
  hailo_data:
  hailo_models:
'''
            
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            self.logger.info(f"Docker Compose 文件已创建: {compose_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Docker Compose 文件创建失败: {e}")
            return False
    
    def setup_complete_docker_environment(self, packages_dir: str) -> bool:
        """设置完整的 Docker 环境"""
        self.logger.info("开始设置完整的 Hailo8 Docker 环境...")
        
        steps = [
            ("安装 Docker", self.install_docker),
            ("配置 Docker 守护进程", self.configure_docker_daemon),
            ("构建 Hailo8 镜像", lambda: self.build_hailo8_image(packages_dir)),
            ("测试容器", self.test_hailo8_container),
            ("创建 Docker Compose", self.create_docker_compose)
        ]
        
        for step_name, step_func in steps:
            self.logger.info(f"执行步骤: {step_name}")
            try:
                if not step_func():
                    self.logger.error(f"步骤失败: {step_name}")
                    return False
                self.logger.info(f"步骤完成: {step_name}")
            except Exception as e:
                self.logger.error(f"步骤异常: {step_name} - {e}")
                return False
        
        self.logger.info("🎉 Hailo8 Docker 环境设置完成！")
        return True
    
    def cleanup_docker_resources(self):
        """清理 Docker 资源"""
        if not self.docker_available:
            return
        
        self.logger.info("清理 Docker 资源...")
        
        try:
            image_name = self.config.get('docker', {}).get('image_name', 'hailo8:latest')
            
            # 停止相关容器
            self.run_command(['docker', 'stop', 'hailo8-container'], timeout=30)
            self.run_command(['docker', 'stop', 'hailo8-jupyter'], timeout=30)
            
            # 删除容器
            self.run_command(['docker', 'rm', 'hailo8-container'])
            self.run_command(['docker', 'rm', 'hailo8-jupyter'])
            
            # 删除镜像
            self.run_command(['docker', 'rmi', image_name])
            
            self.logger.info("Docker 资源清理完成")
            
        except Exception as e:
            self.logger.error(f"Docker 资源清理失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hailo8 Docker 集成管理器")
    parser.add_argument("--packages-dir", default="./De", help="安装包目录路径")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--cleanup", action="store_true", help="清理 Docker 资源")
    parser.add_argument("--test-only", action="store_true", help="仅测试现有容器")
    parser.add_argument("--build-only", action="store_true", help="仅构建镜像")
    
    args = parser.parse_args()
    
    # 检查权限
    if os.geteuid() != 0:
        print("警告: 建议以 root 权限运行以避免权限问题")
    
    manager = DockerHailo8Manager(args.config)
    
    try:
        if args.cleanup:
            manager.cleanup_docker_resources()
        elif args.test_only:
            success = manager.test_hailo8_container()
            sys.exit(0 if success else 1)
        elif args.build_only:
            success = manager.build_hailo8_image(args.packages_dir)
            sys.exit(0 if success else 1)
        else:
            success = manager.setup_complete_docker_environment(args.packages_dir)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()