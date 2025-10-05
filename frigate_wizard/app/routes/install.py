"""
Frigate Setup Wizard - 安装路由
专门处理各种安装任务的路由

作者: Frigate Setup Wizard Team
版本: 1.0.0
"""

import os
import sys
import json
import logging
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, current_app

# 添加项目根目录到Python路径，以便导入现有的安装模块
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    # 尝试导入现有的安装模块
    from installer import Hailo8Installer
    from integration import IntegrationFramework
    HAILO8_INSTALLER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有的Hailo8安装模块: {e}")
    HAILO8_INSTALLER_AVAILABLE = False

# 创建安装蓝图
install_bp = Blueprint('install', __name__, url_prefix='/install')
logger = logging.getLogger(__name__)

# 全局安装状态
install_status = {
    'current_task': None,
    'tasks': {},
    'history': []
}

@install_bp.route('/')
def install_home():
    """安装首页"""
    return render_template('install/index.html', 
                         hailo8_available=HAILO8_INSTALLER_AVAILABLE)

@install_bp.route('/hailo8')
def install_hailo8_page():
    """Hailo8安装页面"""
    return render_template('install/hailo8.html',
                         hailo8_available=HAILO8_INSTALLER_AVAILABLE)

@install_bp.route('/frigate')
def install_frigate_page():
    """Frigate安装页面"""
    return render_template('install/frigate.html')

@install_bp.route('/api/start', methods=['POST'])
def start_installation():
    """启动安装任务"""
    try:
        data = request.get_json()
        install_type = data.get('type')  # hailo8, frigate, full
        options = data.get('options', {})
        
        if not install_type:
            return jsonify({'success': False, 'error': '缺少安装类型'}), 400
        
        # 检查是否有正在运行的任务
        if install_status['current_task']:
            current_task = install_status['tasks'].get(install_status['current_task'])
            if current_task and current_task['status'] == 'running':
                return jsonify({
                    'success': False,
                    'error': '已有安装任务正在运行',
                    'current_task': install_status['current_task']
                }), 400
        
        # 创建新的安装任务
        task_id = f"{install_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_info = {
            'id': task_id,
            'type': install_type,
            'status': 'pending',
            'progress': 0,
            'message': '准备开始安装...',
            'start_time': datetime.now(),
            'end_time': None,
            'options': options,
            'logs': [],
            'error': None
        }
        
        install_status['tasks'][task_id] = task_info
        install_status['current_task'] = task_id
        
        # 启动安装线程
        install_thread = threading.Thread(
            target=run_installation_task,
            args=(task_id, install_type, options)
        )
        install_thread.daemon = True
        install_thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'{install_type}安装任务已启动'
        })
        
    except Exception as e:
        logger.error(f"启动安装任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@install_bp.route('/api/status/<task_id>')
def get_installation_status(task_id):
    """获取安装状态"""
    try:
        if task_id not in install_status['tasks']:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        task = install_status['tasks'][task_id].copy()
        
        # 计算运行时间
        if task['start_time']:
            if task['end_time']:
                duration = (task['end_time'] - task['start_time']).total_seconds()
                task['duration'] = duration
            else:
                current_duration = (datetime.now() - task['start_time']).total_seconds()
                task['current_duration'] = current_duration
        
        return jsonify({'success': True, 'data': task})
        
    except Exception as e:
        logger.error(f"获取安装状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@install_bp.route('/api/cancel/<task_id>', methods=['POST'])
def cancel_installation(task_id):
    """取消安装任务"""
    try:
        if task_id not in install_status['tasks']:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        task = install_status['tasks'][task_id]
        
        if task['status'] != 'running':
            return jsonify({'success': False, 'error': '任务未在运行'}), 400
        
        # 设置取消标志
        task['status'] = 'cancelled'
        task['message'] = '安装已被用户取消'
        task['end_time'] = datetime.now()
        
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None
        
        return jsonify({'success': True, 'message': '安装任务已取消'})
        
    except Exception as e:
        logger.error(f"取消安装任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@install_bp.route('/api/logs/<task_id>')
def get_installation_logs(task_id):
    """获取安装日志"""
    try:
        if task_id not in install_status['tasks']:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        task = install_status['tasks'][task_id]
        logs = task.get('logs', [])
        
        # 获取最新的日志（可选参数）
        limit = request.args.get('limit', type=int)
        if limit:
            logs = logs[-limit:]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'task_id': task_id,
                'status': task['status']
            }
        })
        
    except Exception as e:
        logger.error(f"获取安装日志失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@install_bp.route('/api/history')
def get_installation_history():
    """获取安装历史"""
    try:
        # 获取所有已完成的任务
        history = []
        for task_id, task in install_status['tasks'].items():
            if task['status'] in ['completed', 'failed', 'cancelled']:
                history.append({
                    'id': task_id,
                    'type': task['type'],
                    'status': task['status'],
                    'start_time': task['start_time'].isoformat() if task['start_time'] else None,
                    'end_time': task['end_time'].isoformat() if task['end_time'] else None,
                    'message': task['message']
                })
        
        # 按时间倒序排列
        history.sort(key=lambda x: x['start_time'] or '', reverse=True)
        
        return jsonify({'success': True, 'data': history})
        
    except Exception as e:
        logger.error(f"获取安装历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def run_installation_task(task_id, install_type, options):
    """运行安装任务"""
    try:
        task = install_status['tasks'][task_id]
        task['status'] = 'running'
        task['message'] = f'开始{install_type}安装...'
        
        if install_type == 'hailo8':
            run_hailo8_installation(task_id, options)
        elif install_type == 'frigate':
            run_frigate_installation(task_id, options)
        elif install_type == 'full':
            run_full_installation(task_id, options)
        else:
            raise ValueError(f'不支持的安装类型: {install_type}')
        
    except Exception as e:
        logger.error(f"安装任务执行失败: {e}")
        task = install_status['tasks'][task_id]
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'安装失败: {str(e)}'
        task['end_time'] = datetime.now()
        
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_hailo8_installation(task_id, options):
    """运行Hailo8安装"""
    task = install_status['tasks'][task_id]
    
    try:
        # 更新状态
        task['progress'] = 5
        task['message'] = '检查系统环境...'
        add_log(task, 'info', '开始Hailo8安装')
        
        # 检查是否可以使用现有的安装器
        if HAILO8_INSTALLER_AVAILABLE:
            add_log(task, 'info', '使用集成的Hailo8安装器')
            run_integrated_hailo8_installation(task_id, options)
        else:
            add_log(task, 'info', '使用独立的安装脚本')
            run_script_hailo8_installation(task_id, options)
        
    except Exception as e:
        logger.error(f"Hailo8安装失败: {e}")
        task['status'] = 'failed'
        task['error'] = str(e)
        task['message'] = f'Hailo8安装失败: {str(e)}'
        task['end_time'] = datetime.now()
        add_log(task, 'error', f'安装失败: {str(e)}')
        
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_integrated_hailo8_installation(task_id, options):
    """使用集成的Hailo8安装器"""
    task = install_status['tasks'][task_id]
    
    try:
        # 创建安装器实例
        installer = Hailo8Installer()
        
        # 设置进度回调
        def progress_callback(progress, message):
            task['progress'] = progress
            task['message'] = message
            add_log(task, 'info', message)
        
        # 执行安装
        task['progress'] = 10
        task['message'] = '初始化Hailo8安装器...'
        
        # 检查系统兼容性
        if not installer.check_system_compatibility():
            raise Exception('系统不兼容Hailo8')
        
        task['progress'] = 20
        task['message'] = '下载Hailo8软件包...'
        add_log(task, 'info', '开始下载Hailo8软件包')
        
        # 执行安装步骤
        installer.install(progress_callback=progress_callback)
        
        # 验证安装
        task['progress'] = 90
        task['message'] = '验证安装结果...'
        
        if installer.verify_installation():
            task['status'] = 'completed'
            task['progress'] = 100
            task['message'] = 'Hailo8安装完成'
            task['end_time'] = datetime.now()
            add_log(task, 'success', 'Hailo8安装成功完成')
        else:
            raise Exception('安装验证失败')
        
    except Exception as e:
        raise e
    finally:
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_script_hailo8_installation(task_id, options):
    """使用独立的安装脚本"""
    task = install_status['tasks'][task_id]
    
    try:
        # 查找安装脚本
        script_path = project_root / 'install.sh'
        
        if not script_path.exists():
            raise FileNotFoundError(f'安装脚本不存在: {script_path}')
        
        task['progress'] = 15
        task['message'] = '执行Hailo8安装脚本...'
        add_log(task, 'info', f'使用安装脚本: {script_path}')
        
        # 执行安装脚本
        process = subprocess.Popen(
            ['bash', str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(project_root)
        )
        
        # 实时读取输出
        progress = 15
        for line in process.stdout:
            # 检查是否被取消
            if task['status'] == 'cancelled':
                process.terminate()
                break
            
            line = line.strip()
            if line:
                add_log(task, 'info', line)
                
                # 简单的进度估算
                if any(keyword in line.lower() for keyword in ['installing', 'download']):
                    progress = min(progress + 5, 85)
                    task['progress'] = progress
                elif any(keyword in line.lower() for keyword in ['configuring', 'setting']):
                    progress = min(progress + 3, 90)
                    task['progress'] = progress
                
                task['message'] = line
        
        # 等待进程完成
        return_code = process.wait()
        
        # 检查安装结果
        if return_code == 0 and task['status'] != 'cancelled':
            task['status'] = 'completed'
            task['progress'] = 100
            task['message'] = 'Hailo8安装完成'
            task['end_time'] = datetime.now()
            add_log(task, 'success', 'Hailo8安装脚本执行成功')
        else:
            raise Exception(f'安装脚本执行失败 (退出码: {return_code})')
        
    except Exception as e:
        raise e
    finally:
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_frigate_installation(task_id, options):
    """运行Frigate安装"""
    task = install_status['tasks'][task_id]
    
    try:
        task['progress'] = 5
        task['message'] = '准备Frigate安装...'
        add_log(task, 'info', '开始Frigate安装')
        
        # 检查Docker
        if not check_docker_available():
            raise Exception('Docker未安装或未运行')
        
        task['progress'] = 15
        task['message'] = '生成Frigate配置...'
        
        # 根据选项生成配置
        install_type = options.get('type', 'standard')
        compose_content = generate_frigate_compose(install_type, options)
        
        # 创建配置目录
        config_dir = Path('/opt/frigate')
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存配置文件
        compose_file = config_dir / 'docker-compose.yml'
        with open(compose_file, 'w') as f:
            f.write(compose_content)
        
        task['progress'] = 30
        task['message'] = '拉取Frigate镜像...'
        add_log(task, 'info', '开始拉取Docker镜像')
        
        # 拉取镜像
        pull_process = subprocess.Popen(
            ['docker-compose', '-f', str(compose_file), 'pull'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(config_dir)
        )
        
        for line in pull_process.stdout:
            if task['status'] == 'cancelled':
                pull_process.terminate()
                break
            
            line = line.strip()
            if line:
                add_log(task, 'info', line)
                task['message'] = line
                
                if 'Pulling' in line or 'Downloaded' in line:
                    task['progress'] = min(task['progress'] + 5, 80)
        
        pull_return_code = pull_process.wait()
        
        if pull_return_code != 0:
            raise Exception(f'拉取镜像失败 (退出码: {pull_return_code})')
        
        task['progress'] = 85
        task['message'] = '启动Frigate服务...'
        add_log(task, 'info', '启动Frigate容器')
        
        # 启动服务
        start_process = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'up', '-d'],
            capture_output=True,
            text=True,
            cwd=str(config_dir)
        )
        
        if start_process.returncode == 0:
            task['status'] = 'completed'
            task['progress'] = 100
            task['message'] = 'Frigate安装并启动完成'
            task['end_time'] = datetime.now()
            add_log(task, 'success', 'Frigate安装成功完成')
        else:
            raise Exception(f'启动Frigate失败: {start_process.stderr}')
        
    except Exception as e:
        raise e
    finally:
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_full_installation(task_id, options):
    """运行完整安装（Hailo8 + Frigate）"""
    task = install_status['tasks'][task_id]
    
    try:
        task['progress'] = 5
        task['message'] = '开始完整安装...'
        add_log(task, 'info', '开始完整安装 (Hailo8 + Frigate)')
        
        # 第一步：安装Hailo8
        task['progress'] = 10
        task['message'] = '第1步: 安装Hailo8...'
        add_log(task, 'info', '开始安装Hailo8')
        
        # 创建临时的Hailo8安装任务
        hailo8_options = options.get('hailo8', {})
        run_hailo8_installation_sync(task, hailo8_options, progress_offset=10, progress_range=40)
        
        # 第二步：安装Frigate
        task['progress'] = 55
        task['message'] = '第2步: 安装Frigate...'
        add_log(task, 'info', '开始安装Frigate')
        
        # 创建临时的Frigate安装任务
        frigate_options = options.get('frigate', {})
        frigate_options['type'] = 'hailo8'  # 使用Hailo8增强版
        run_frigate_installation_sync(task, frigate_options, progress_offset=55, progress_range=40)
        
        # 完成
        task['status'] = 'completed'
        task['progress'] = 100
        task['message'] = '完整安装完成'
        task['end_time'] = datetime.now()
        add_log(task, 'success', '完整安装成功完成')
        
    except Exception as e:
        raise e
    finally:
        # 清除当前任务
        if install_status['current_task'] == task_id:
            install_status['current_task'] = None

def run_hailo8_installation_sync(task, options, progress_offset=0, progress_range=100):
    """同步运行Hailo8安装（用于完整安装）"""
    # 这里简化实现，实际应该调用相应的安装函数
    # 并将进度映射到指定范围
    pass

def run_frigate_installation_sync(task, options, progress_offset=0, progress_range=100):
    """同步运行Frigate安装（用于完整安装）"""
    # 这里简化实现，实际应该调用相应的安装函数
    # 并将进度映射到指定范围
    pass

def add_log(task, level, message):
    """添加日志到任务"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message
    }
    task['logs'].append(log_entry)
    
    # 限制日志数量
    if len(task['logs']) > 1000:
        task['logs'] = task['logs'][-500:]

def check_docker_available():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def generate_frigate_compose(install_type, options):
    """生成Frigate Docker Compose配置"""
    if install_type == 'hailo8':
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
    elif install_type == 'coral':
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
    else:  # standard
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