"""
Frigate Setup Wizard - 主要路由
处理首页、系统状态、配置页面等基本路由
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import docker
import os
import subprocess
import json
from pathlib import Path

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页 - 显示安装向导主界面"""
    
    # 检查系统状态
    system_status = check_system_status()
    
    # 检查Frigate状态
    frigate_status = check_frigate_status()
    
    # 检查Hailo8状态
    hailo8_status = check_hailo8_status()
    
    return render_template('index.html', 
                         system_status=system_status,
                         frigate_status=frigate_status,
                         hailo8_status=hailo8_status)

@main_bp.route('/dashboard')
def dashboard():
    """仪表板 - 显示系统整体状态"""
    
    # 获取详细的系统信息
    system_info = get_detailed_system_info()
    
    # 获取安装历史
    install_history = get_install_history()
    
    # 获取性能监控数据
    performance_data = get_performance_data()
    
    return render_template('dashboard.html',
                         system_info=system_info,
                         install_history=install_history,
                         performance_data=performance_data)

@main_bp.route('/config')
def config():
    """配置页面 - Frigate配置管理"""
    
    # 读取现有配置
    config_data = load_frigate_config()
    
    # 获取可用的摄像头
    available_cameras = detect_cameras()
    
    # 获取硬件加速选项
    hardware_options = get_hardware_acceleration_options()
    
    return render_template('config.html',
                         config_data=config_data,
                         available_cameras=available_cameras,
                         hardware_options=hardware_options)

@main_bp.route('/hardware')
def hardware():
    """硬件检测页面"""
    
    # 检测系统硬件
    hardware_info = detect_hardware()
    
    # 检测GPU支持
    gpu_info = detect_gpu_support()
    
    # 检测TPU支持
    tpu_info = detect_tpu_support()
    
    return render_template('hardware.html',
                         hardware_info=hardware_info,
                         gpu_info=gpu_info,
                         tpu_info=tpu_info)

@main_bp.route('/logs')
def logs():
    """日志查看页面"""
    
    # 获取可用的日志文件
    log_files = get_available_logs()
    
    return render_template('logs.html', log_files=log_files)

@main_bp.route('/api/logs/<log_type>')
def get_logs(log_type):
    """获取指定类型的日志"""
    
    try:
        lines = int(request.args.get('lines', 100))
        
        if log_type == 'frigate':
            logs = get_frigate_logs(lines)
        elif log_type == 'hailo8':
            logs = get_hailo8_logs(lines)
        elif log_type == 'system':
            logs = get_system_logs(lines)
        elif log_type == 'wizard':
            logs = get_wizard_logs(lines)
        else:
            return jsonify({'error': '未知的日志类型'}), 400
        
        return jsonify({'logs': logs})
        
    except Exception as e:
        current_app.logger.error(f'获取日志失败: {e}')
        return jsonify({'error': str(e)}), 500

# 辅助函数

def check_system_status():
    """检查系统基本状态"""
    
    status = {
        'docker': False,
        'docker_compose': False,
        'python': False,
        'git': False,
        'disk_space': 0,
        'memory_usage': 0,
        'cpu_usage': 0
    }
    
    try:
        # 检查Docker
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        status['docker'] = result.returncode == 0
        
        # 检查Docker Compose
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=5)
        status['docker_compose'] = result.returncode == 0
        
        # 检查Python
        result = subprocess.run(['python3', '--version'], 
                              capture_output=True, text=True, timeout=5)
        status['python'] = result.returncode == 0
        
        # 检查Git
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, timeout=5)
        status['git'] = result.returncode == 0
        
        # 获取系统资源使用情况
        import psutil
        status['disk_space'] = psutil.disk_usage('/').percent
        status['memory_usage'] = psutil.virtual_memory().percent
        status['cpu_usage'] = psutil.cpu_percent(interval=1)
        
    except Exception as e:
        current_app.logger.error(f'检查系统状态失败: {e}')
    
    return status

def check_frigate_status():
    """检查Frigate状态"""
    
    status = {
        'installed': False,
        'running': False,
        'version': None,
        'config_exists': False,
        'web_accessible': False
    }
    
    try:
        # 检查Docker容器
        client = docker.from_env()
        
        try:
            container = client.containers.get('frigate')
            status['installed'] = True
            status['running'] = container.status == 'running'
            
            # 获取版本信息
            if 'frigate' in container.image.tags[0]:
                status['version'] = container.image.tags[0].split(':')[-1]
                
        except docker.errors.NotFound:
            pass
        
        # 检查配置文件
        config_path = Path(current_app.config['FRIGATE_CONFIG_DIR']) / 'config.yml'
        status['config_exists'] = config_path.exists()
        
        # 检查Web界面可访问性
        if status['running']:
            import requests
            try:
                response = requests.get('http://localhost:5000', timeout=5)
                status['web_accessible'] = response.status_code == 200
            except:
                pass
                
    except Exception as e:
        current_app.logger.error(f'检查Frigate状态失败: {e}')
    
    return status

def check_hailo8_status():
    """检查Hailo8状态"""
    
    status = {
        'hardware_detected': False,
        'driver_installed': False,
        'runtime_available': False,
        'models_available': False,
        'performance_good': False
    }
    
    try:
        # 检查硬件
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
        if 'Hailo' in result.stdout:
            status['hardware_detected'] = True
        
        # 检查驱动
        result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
        if 'hailo' in result.stdout.lower():
            status['driver_installed'] = True
        
        # 检查运行时
        hailo_install_dir = Path(current_app.config['HAILO8_INSTALL_DIR'])
        if hailo_install_dir.exists():
            status['runtime_available'] = True
            
            # 检查模型文件
            models_dir = hailo_install_dir / 'models'
            if models_dir.exists() and list(models_dir.glob('*.hef')):
                status['models_available'] = True
        
        # 简单性能测试
        if status['hardware_detected'] and status['driver_installed']:
            # 这里可以添加简单的性能测试
            status['performance_good'] = True
            
    except Exception as e:
        current_app.logger.error(f'检查Hailo8状态失败: {e}')
    
    return status

def get_detailed_system_info():
    """获取详细系统信息"""
    
    import platform
    import psutil
    
    info = {
        'os': platform.platform(),
        'kernel': platform.release(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'cpu': {
            'model': platform.processor(),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'usage': psutil.cpu_percent(interval=1)
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'usage': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'free': psutil.disk_usage('/').free,
            'usage': psutil.disk_usage('/').percent
        }
    }
    
    return info

def get_install_history():
    """获取安装历史"""
    
    history_file = Path(current_app.instance_path) / 'install_history.json'
    
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f'读取安装历史失败: {e}')
    
    return []

def get_performance_data():
    """获取性能监控数据"""
    
    # 这里可以集成更复杂的性能监控
    # 暂时返回基本的系统性能数据
    
    import psutil
    
    return {
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
        'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
    }

def load_frigate_config():
    """加载Frigate配置"""
    
    config_path = Path(current_app.config['FRIGATE_CONFIG_DIR']) / 'config.yml'
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            current_app.logger.error(f'读取Frigate配置失败: {e}')
    
    return {}

def detect_cameras():
    """检测可用摄像头"""
    
    cameras = []
    
    try:
        # 检测USB摄像头
        for i in range(10):  # 检查前10个设备
            device_path = f'/dev/video{i}'
            if os.path.exists(device_path):
                cameras.append({
                    'type': 'usb',
                    'device': device_path,
                    'name': f'USB Camera {i}'
                })
        
        # 这里可以添加RTSP摄像头检测逻辑
        
    except Exception as e:
        current_app.logger.error(f'检测摄像头失败: {e}')
    
    return cameras

def get_hardware_acceleration_options():
    """获取硬件加速选项"""
    
    options = {
        'cpu': True,  # CPU总是可用
        'vaapi': False,
        'nvidia': False,
        'hailo8': False,
        'coral': False
    }
    
    try:
        # 检查VAAPI支持
        if os.path.exists('/dev/dri'):
            options['vaapi'] = True
        
        # 检查NVIDIA GPU
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            options['nvidia'] = True
        
        # 检查Hailo8
        if current_app.config['HAILO8_ENABLED']:
            hailo_status = check_hailo8_status()
            options['hailo8'] = hailo_status['hardware_detected']
        
        # 检查Coral TPU
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
        if 'Google Inc.' in result.stdout and 'Coral' in result.stdout:
            options['coral'] = True
            
    except Exception as e:
        current_app.logger.error(f'检测硬件加速选项失败: {e}')
    
    return options

def detect_hardware():
    """检测系统硬件"""
    
    hardware = {
        'cpu': {},
        'memory': {},
        'storage': {},
        'usb_devices': [],
        'pci_devices': []
    }
    
    try:
        import psutil
        
        # CPU信息
        hardware['cpu'] = {
            'model': platform.processor(),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
        }
        
        # 内存信息
        mem = psutil.virtual_memory()
        hardware['memory'] = {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percentage': mem.percent
        }
        
        # 存储信息
        disk = psutil.disk_usage('/')
        hardware['storage'] = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percentage': (disk.used / disk.total) * 100
        }
        
        # USB设备
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    hardware['usb_devices'].append(line.strip())
        
        # PCI设备
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    hardware['pci_devices'].append(line.strip())
                    
    except Exception as e:
        current_app.logger.error(f'检测硬件失败: {e}')
    
    return hardware

def detect_gpu_support():
    """检测GPU支持"""
    
    gpu_info = {
        'nvidia': {'available': False, 'devices': []},
        'amd': {'available': False, 'devices': []},
        'intel': {'available': False, 'devices': []}
    }
    
    try:
        # 检测NVIDIA GPU
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpu_info['nvidia']['available'] = True
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    gpu_info['nvidia']['devices'].append(line.strip())
        
        # 检测AMD GPU (通过lspci)
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'AMD' in line and ('VGA' in line or 'Display' in line):
                    gpu_info['amd']['available'] = True
                    gpu_info['amd']['devices'].append(line.strip())
                elif 'Intel' in line and ('VGA' in line or 'Display' in line):
                    gpu_info['intel']['available'] = True
                    gpu_info['intel']['devices'].append(line.strip())
                    
    except Exception as e:
        current_app.logger.error(f'检测GPU支持失败: {e}')
    
    return gpu_info

def detect_tpu_support():
    """检测TPU支持"""
    
    tpu_info = {
        'hailo8': {'available': False, 'devices': []},
        'coral': {'available': False, 'devices': []},
        'other': {'available': False, 'devices': []}
    }
    
    try:
        # 检测Hailo8
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Hailo' in line:
                    tpu_info['hailo8']['available'] = True
                    tpu_info['hailo8']['devices'].append(line.strip())
        
        # 检测Coral TPU
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Google Inc.' in line and 'Coral' in line:
                    tpu_info['coral']['available'] = True
                    tpu_info['coral']['devices'].append(line.strip())
                    
    except Exception as e:
        current_app.logger.error(f'检测TPU支持失败: {e}')
    
    return tpu_info

def get_available_logs():
    """获取可用的日志文件"""
    
    logs = {
        'wizard': '向导日志',
        'frigate': 'Frigate日志',
        'hailo8': 'Hailo8日志',
        'system': '系统日志'
    }
    
    return logs

def get_frigate_logs(lines=100):
    """获取Frigate日志"""
    
    try:
        client = docker.from_env()
        container = client.containers.get('frigate')
        logs = container.logs(tail=lines).decode('utf-8')
        return logs.split('\n')
    except Exception as e:
        current_app.logger.error(f'获取Frigate日志失败: {e}')
        return [f'获取日志失败: {e}']

def get_hailo8_logs(lines=100):
    """获取Hailo8日志"""
    
    try:
        log_file = Path('/var/log/hailo8.log')
        if log_file.exists():
            result = subprocess.run(['tail', '-n', str(lines), str(log_file)], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.split('\n')
        return ['Hailo8日志文件不存在']
    except Exception as e:
        current_app.logger.error(f'获取Hailo8日志失败: {e}')
        return [f'获取日志失败: {e}']

def get_system_logs(lines=100):
    """获取系统日志"""
    
    try:
        result = subprocess.run(['journalctl', '-n', str(lines), '--no-pager'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.split('\n')
        return ['无法获取系统日志']
    except Exception as e:
        current_app.logger.error(f'获取系统日志失败: {e}')
        return [f'获取日志失败: {e}']

def get_wizard_logs(lines=100):
    """获取向导日志"""
    
    try:
        log_file = Path(current_app.config['LOG_FILE'])
        if log_file.exists():
            result = subprocess.run(['tail', '-n', str(lines), str(log_file)], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.split('\n')
        return ['向导日志文件不存在']
    except Exception as e:
        current_app.logger.error(f'获取向导日志失败: {e}')
        return [f'获取日志失败: {e}']