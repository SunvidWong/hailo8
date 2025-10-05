"""
Frigate Setup Wizard - API路由
处理所有API请求，包括Hailo8安装、系统状态、配置管理等

作者: Frigate Setup Wizard Team
版本: 1.0.0
"""

import os
import json
import logging
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# 全局状态变量
installation_status = {
    'hailo8': {
        'status': 'idle',  # idle, running, completed, failed
        'progress': 0,
        'message': '',
        'start_time': None,
        'end_time': None,
        'logs': []
    },
    'frigate': {
        'status': 'idle',
        'progress': 0,
        'message': '',
        'start_time': None,
        'end_time': None,
        'logs': []
    }
}

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status = {
            'system': {
                'online': True,
                'timestamp': datetime.now().isoformat(),
                'uptime': get_system_uptime()
            },
            'frigate': {
                'installed': check_frigate_installed(),
                'running': check_frigate_running(),
                'version': get_frigate_version()
            },
            'hailo8': {
                'detected': check_hailo8_hardware(),
                'installed': check_hailo8_installed(),
                'driver_version': get_hailo8_driver_version()
            },
            'docker': {
                'installed': check_docker_installed(),
                'running': check_docker_running(),
                'version': get_docker_version()
            }
        }
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/hardware', methods=['GET'])
def get_hardware_info():
    """获取硬件信息"""
    try:
        import psutil
        
        hardware = {
            'cpu': {
                'model': get_cpu_model(),
                'cores': psutil.cpu_count(),
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
            },
            'hailo8': {
                'detected': check_hailo8_hardware(),
                'devices': get_hailo8_devices(),
                'temperature': get_hailo8_temperature()
            },
            'coral': {
                'detected': check_coral_hardware(),
                'devices': get_coral_devices()
            }
        }
        return jsonify({'success': True, 'data': hardware})
    except Exception as e:
        logger.error(f"获取硬件信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/install/hailo8', methods=['POST'])
def install_hailo8():
    """启动Hailo8安装"""
    try:
        if installation_status['hailo8']['status'] == 'running':
            return jsonify({
                'success': False, 
                'error': 'Hailo8安装正在进行中'
            }), 400
        
        # 获取安装选项
        options = request.get_json() or {}
        install_type = options.get('type', 'standard')
        force_reinstall = options.get('force', False)
        
        # 检查是否已安装
        if check_hailo8_installed() and not force_reinstall:
            return jsonify({
                'success': False,
                'error': 'Hailo8已安装，使用force=true强制重新安装'
            }), 400
        
        # 启动安装线程
        install_thread = threading.Thread(
            target=run_hailo8_installation,
            args=(install_type, options)
        )
        install_thread.daemon = True
        install_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Hailo8安装已启动',
            'install_id': f"hailo8_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        })
        
    except Exception as e:
        logger.error(f"启动Hailo8安装失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/install/frigate', methods=['POST'])
def install_frigate():
    """启动Frigate安装"""
    try:
        if installation_status['frigate']['status'] == 'running':
            return jsonify({
                'success': False,
                'error': 'Frigate安装正在进行中'
            }), 400
        
        # 获取安装选项
        options = request.get_json() or {}
        install_type = options.get('type', 'standard')  # standard, hailo8, coral
        
        # 启动安装线程
        install_thread = threading.Thread(
            target=run_frigate_installation,
            args=(install_type, options)
        )
        install_thread.daemon = True
        install_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Frigate安装已启动',
            'install_id': f"frigate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        })
        
    except Exception as e:
        logger.error(f"启动Frigate安装失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/install/status/<component>', methods=['GET'])
def get_install_status(component):
    """获取安装状态"""
    try:
        if component not in installation_status:
            return jsonify({'success': False, 'error': '无效的组件'}), 400
        
        status = installation_status[component].copy()
        
        # 计算安装时间
        if status['start_time'] and status['end_time']:
            duration = (status['end_time'] - status['start_time']).total_seconds()
            status['duration'] = duration
        elif status['start_time']:
            duration = (datetime.now() - status['start_time']).total_seconds()
            status['current_duration'] = duration
        
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        logger.error(f"获取安装状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/install/cancel/<component>', methods=['POST'])
def cancel_installation(component):
    """取消安装"""
    try:
        if component not in installation_status:
            return jsonify({'success': False, 'error': '无效的组件'}), 400
        
        if installation_status[component]['status'] != 'running':
            return jsonify({'success': False, 'error': '没有正在运行的安装'}), 400
        
        # 设置取消标志
        installation_status[component]['status'] = 'cancelled'
        installation_status[component]['message'] = '安装已被用户取消'
        installation_status[component]['end_time'] = datetime.now()
        
        return jsonify({'success': True, 'message': f'{component}安装已取消'})
        
    except Exception as e:
        logger.error(f"取消安装失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/logs/<log_type>', methods=['GET'])
def get_logs(log_type):
    """获取日志"""
    try:
        lines = int(request.args.get('lines', 100))
        
        log_files = {
            'system': '/var/log/syslog',
            'frigate': '/opt/frigate/logs/frigate.log',
            'hailo8': '/var/log/hailo8.log',
            'wizard': 'frigate_wizard.log'
        }
        
        if log_type not in log_files:
            return jsonify({'success': False, 'error': '无效的日志类型'}), 400
        
        log_file = log_files[log_type]
        if not os.path.exists(log_file):
            return jsonify({'success': True, 'data': {'logs': [], 'message': '日志文件不存在'}})
        
        # 读取日志文件的最后N行
        logs = read_log_tail(log_file, lines)
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'file': log_file,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/config/frigate', methods=['GET', 'POST'])
def manage_frigate_config():
    """管理Frigate配置"""
    try:
        config_file = '/opt/frigate/config/config.yml'
        
        if request.method == 'GET':
            # 读取配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = f.read()
                return jsonify({'success': True, 'data': {'config': config}})
            else:
                return jsonify({'success': True, 'data': {'config': '', 'message': '配置文件不存在'}})
        
        elif request.method == 'POST':
            # 保存配置
            data = request.get_json()
            config_content = data.get('config', '')
            
            # 创建配置目录
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 备份现有配置
            if os.path.exists(config_file):
                backup_file = f"{config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(config_file, backup_file)
            
            # 保存新配置
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            return jsonify({'success': True, 'message': '配置已保存'})
            
    except Exception as e:
        logger.error(f"管理Frigate配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 辅助函数
def get_system_uptime():
    """获取系统运行时间"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return int(uptime_seconds)
    except:
        return 0

def check_frigate_installed():
    """检查Frigate是否已安装"""
    try:
        result = subprocess.run(['docker', 'images', 'ghcr.io/blakeblackshear/frigate'], 
                              capture_output=True, text=True)
        return 'frigate' in result.stdout
    except:
        return False

def check_frigate_running():
    """检查Frigate是否正在运行"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=frigate'], 
                              capture_output=True, text=True)
        return 'frigate' in result.stdout
    except:
        return False

def get_frigate_version():
    """获取Frigate版本"""
    try:
        result = subprocess.run(['docker', 'inspect', 'frigate', '--format', '{{.Config.Labels.version}}'], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except:
        return 'unknown'

def check_hailo8_hardware():
    """检查Hailo8硬件"""
    try:
        # 检查PCIe设备
        result = subprocess.run(['lspci'], capture_output=True, text=True)
        return 'Hailo' in result.stdout
    except:
        return False

def check_hailo8_installed():
    """检查Hailo8软件是否已安装"""
    try:
        result = subprocess.run(['hailortcli', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_hailo8_driver_version():
    """获取Hailo8驱动版本"""
    try:
        result = subprocess.run(['hailortcli', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return 'unknown'
    except:
        return 'unknown'

def check_docker_installed():
    """检查Docker是否已安装"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_docker_running():
    """检查Docker是否正在运行"""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_docker_version():
    """获取Docker版本"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split()[2].rstrip(',')
        return 'unknown'
    except:
        return 'unknown'

def get_cpu_model():
    """获取CPU型号"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    return line.split(':')[1].strip()
        return 'unknown'
    except:
        return 'unknown'

def get_hailo8_devices():
    """获取Hailo8设备列表"""
    try:
        result = subprocess.run(['hailortcli', 'scan'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []
    except:
        return []

def get_hailo8_temperature():
    """获取Hailo8温度"""
    try:
        # 这里需要根据实际的Hailo8 API来实现
        return None
    except:
        return None

def check_coral_hardware():
    """检查Coral硬件"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        return 'Google Inc.' in result.stdout and 'Coral' in result.stdout
    except:
        return False

def get_coral_devices():
    """获取Coral设备列表"""
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        devices = []
        for line in result.stdout.split('\n'):
            if 'Google Inc.' in line and 'Coral' in line:
                devices.append(line.strip())
        return devices
    except:
        return []

def read_log_tail(file_path, lines=100):
    """读取日志文件的最后N行"""
    try:
        result = subprocess.run(['tail', '-n', str(lines), file_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []
    except:
        return []

def run_hailo8_installation(install_type, options):
    """运行Hailo8安装"""
    try:
        # 更新状态
        installation_status['hailo8']['status'] = 'running'
        installation_status['hailo8']['progress'] = 0
        installation_status['hailo8']['message'] = '开始安装Hailo8...'
        installation_status['hailo8']['start_time'] = datetime.now()
        installation_status['hailo8']['logs'] = []
        
        # 获取现有的安装脚本路径
        script_path = Path(__file__).parent.parent.parent / 'install.sh'
        
        if not script_path.exists():
            raise FileNotFoundError(f"安装脚本不存在: {script_path}")
        
        # 运行安装脚本
        process = subprocess.Popen(
            ['bash', str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时读取输出
        for line in process.stdout:
            if installation_status['hailo8']['status'] == 'cancelled':
                process.terminate()
                break
                
            line = line.strip()
            if line:
                installation_status['hailo8']['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line
                })
                
                # 更新进度（简单的进度估算）
                if 'Installing' in line:
                    installation_status['hailo8']['progress'] = min(installation_status['hailo8']['progress'] + 10, 90)
                elif 'Configuring' in line:
                    installation_status['hailo8']['progress'] = min(installation_status['hailo8']['progress'] + 5, 95)
                
                installation_status['hailo8']['message'] = line
        
        # 等待进程完成
        return_code = process.wait()
        
        # 更新最终状态
        installation_status['hailo8']['end_time'] = datetime.now()
        
        if return_code == 0 and installation_status['hailo8']['status'] != 'cancelled':
            installation_status['hailo8']['status'] = 'completed'
            installation_status['hailo8']['progress'] = 100
            installation_status['hailo8']['message'] = 'Hailo8安装完成'
        else:
            installation_status['hailo8']['status'] = 'failed'
            installation_status['hailo8']['message'] = f'Hailo8安装失败 (退出码: {return_code})'
        
    except Exception as e:
        logger.error(f"Hailo8安装过程出错: {e}")
        installation_status['hailo8']['status'] = 'failed'
        installation_status['hailo8']['message'] = f'安装出错: {str(e)}'
        installation_status['hailo8']['end_time'] = datetime.now()

def run_frigate_installation(install_type, options):
    """运行Frigate安装"""
    try:
        # 更新状态
        installation_status['frigate']['status'] = 'running'
        installation_status['frigate']['progress'] = 0
        installation_status['frigate']['message'] = '开始安装Frigate...'
        installation_status['frigate']['start_time'] = datetime.now()
        installation_status['frigate']['logs'] = []
        
        # 根据安装类型选择不同的安装方式
        if install_type == 'hailo8':
            # 安装支持Hailo8的Frigate版本
            docker_compose_content = generate_frigate_compose_hailo8(options)
        elif install_type == 'coral':
            # 安装支持Coral的Frigate版本
            docker_compose_content = generate_frigate_compose_coral(options)
        else:
            # 标准安装
            docker_compose_content = generate_frigate_compose_standard(options)
        
        # 创建配置目录
        config_dir = Path('/opt/frigate')
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存docker-compose.yml
        compose_file = config_dir / 'docker-compose.yml'
        with open(compose_file, 'w') as f:
            f.write(docker_compose_content)
        
        installation_status['frigate']['progress'] = 20
        installation_status['frigate']['message'] = '配置文件已创建'
        
        # 拉取Docker镜像
        process = subprocess.Popen(
            ['docker-compose', '-f', str(compose_file), 'pull'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(config_dir)
        )
        
        for line in process.stdout:
            if installation_status['frigate']['status'] == 'cancelled':
                process.terminate()
                break
                
            line = line.strip()
            if line:
                installation_status['frigate']['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line
                })
                installation_status['frigate']['message'] = line
                
                if 'Pulling' in line:
                    installation_status['frigate']['progress'] = min(installation_status['frigate']['progress'] + 10, 80)
        
        return_code = process.wait()
        
        if return_code == 0:
            installation_status['frigate']['progress'] = 90
            installation_status['frigate']['message'] = '启动Frigate服务...'
            
            # 启动服务
            start_process = subprocess.run(
                ['docker-compose', '-f', str(compose_file), 'up', '-d'],
                capture_output=True,
                text=True,
                cwd=str(config_dir)
            )
            
            if start_process.returncode == 0:
                installation_status['frigate']['status'] = 'completed'
                installation_status['frigate']['progress'] = 100
                installation_status['frigate']['message'] = 'Frigate安装并启动完成'
            else:
                installation_status['frigate']['status'] = 'failed'
                installation_status['frigate']['message'] = f'启动Frigate失败: {start_process.stderr}'
        else:
            installation_status['frigate']['status'] = 'failed'
            installation_status['frigate']['message'] = f'拉取镜像失败 (退出码: {return_code})'
        
        installation_status['frigate']['end_time'] = datetime.now()
        
    except Exception as e:
        logger.error(f"Frigate安装过程出错: {e}")
        installation_status['frigate']['status'] = 'failed'
        installation_status['frigate']['message'] = f'安装出错: {str(e)}'
        installation_status['frigate']['end_time'] = datetime.now()

def generate_frigate_compose_standard(options):
    """生成标准Frigate Docker Compose配置"""
    return """version: "3.9"
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "64mb"
    devices:
      - /dev/bus/usb:/dev/bus/usb
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/config
      - ./storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"
      - "8554:8554"
      - "8555:8555/tcp"
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "password"
"""

def generate_frigate_compose_hailo8(options):
    """生成支持Hailo8的Frigate Docker Compose配置"""
    return """version: "3.9"
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "64mb"
    devices:
      - /dev/bus/usb:/dev/bus/usb
      - /dev/hailo0:/dev/hailo0
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/config
      - ./storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"
      - "8554:8554"
      - "8555:8555/tcp"
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "password"
      LIBVA_DRIVER_NAME: "hailo"
"""

def generate_frigate_compose_coral(options):
    """生成支持Coral的Frigate Docker Compose配置"""
    return """version: "3.9"
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "64mb"
    devices:
      - /dev/bus/usb:/dev/bus/usb
      - /dev/apex_0:/dev/apex_0
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/config
      - ./storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"
      - "8554:8554"
      - "8555:8555/tcp"
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "password"
"""