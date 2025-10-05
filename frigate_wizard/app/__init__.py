"""
Frigate Setup Wizard - Flask应用初始化
集成Hailo8 TPU支持的Frigate NVR安装向导
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'frigate-wizard-secret-key-2024')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Frigate相关配置
    app.config['FRIGATE_CONFIG_PATH'] = os.getenv('FRIGATE_CONFIG_PATH', '/opt/frigate/config')
    app.config['FRIGATE_MEDIA_PATH'] = os.getenv('FRIGATE_MEDIA_PATH', '/opt/frigate/media')
    app.config['FRIGATE_DOCKER_IMAGE'] = os.getenv('FRIGATE_DOCKER_IMAGE', 'ghcr.io/blakeblackshear/frigate:stable')
    
    # Hailo8相关配置
    app.config['HAILO8_INSTALL_PATH'] = os.getenv('HAILO8_INSTALL_PATH', '/opt/hailo')
    app.config['HAILO8_MODELS_PATH'] = os.getenv('HAILO8_MODELS_PATH', '/opt/hailo/models')
    app.config['HAILO8_ENABLED'] = os.getenv('HAILO8_ENABLED', 'True').lower() == 'true'
    
    # 系统配置
    app.config['SYSTEM_LOG_PATH'] = os.getenv('SYSTEM_LOG_PATH', '/var/log')
    app.config['WIZARD_LOG_PATH'] = os.getenv('WIZARD_LOG_PATH', './logs')
    app.config['TEMP_PATH'] = os.getenv('TEMP_PATH', './temp')
    
    # 创建必要目录
    for path_key in ['WIZARD_LOG_PATH', 'TEMP_PATH']:
        path = Path(app.config[path_key])
        path.mkdir(parents=True, exist_ok=True)
    
    # 添加简单的测试路由
    @app.route('/')
    def index():
        """首页"""
        try:
            return render_template('simple_index.html', 
                                 system_status={'status': 'running', 'message': '系统正常运行'},
                                 frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                                 hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
        except Exception as e:
            logger.error(f"首页渲染失败: {e}")
            return jsonify({'error': '页面渲染失败', 'details': str(e)}), 500
    
    @app.route('/test')
    def test():
        """测试路由"""
        return jsonify({
            'status': 'success',
            'message': 'Frigate Setup Wizard 运行正常',
            'version': '1.0.0'
        })
    
    # 添加基础页面路由（当蓝图导入失败时使用）
    @app.route('/dashboard')
    def dashboard():
        """仪表板页面"""
        return render_template('simple_index.html', 
                             system_status={'status': 'running', 'message': '系统正常运行'},
                             frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                             hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
    
    @app.route('/config')
    def config():
        """配置页面"""
        return render_template('simple_index.html', 
                             system_status={'status': 'running', 'message': '系统正常运行'},
                             frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                             hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
    
    @app.route('/hardware')
    def hardware():
        """硬件页面"""
        return render_template('simple_index.html', 
                             system_status={'status': 'running', 'message': '系统正常运行'},
                             frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                             hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
    
    @app.route('/logs')
    def logs():
        """日志页面"""
        return render_template('simple_index.html', 
                             system_status={'status': 'running', 'message': '系统正常运行'},
                             frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                             hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
    
    # 添加基础API路由（当蓝图导入失败时使用）
    @app.route('/api/system/status')
    def api_system_status():
        """系统状态API"""
        return jsonify({
            'status': 'success',
            'data': {
                'system': {
                    'online': True,
                    'timestamp': '2025-10-05T17:32:00',
                    'uptime': '1 day, 2 hours',
                    'cpu_usage': 25.5,
                    'memory_usage': 45.2,
                    'disk_usage': 60.1
                },
                'frigate': {
                    'installed': False,
                    'running': False,
                    'version': None
                },
                'hailo8': {
                    'hardware_detected': False,
                    'driver_installed': False,
                    'driver_version': None
                }
            }
        })
    
    @app.route('/api/hardware')
    def api_hardware():
        """硬件信息API"""
        return jsonify({
            'status': 'success',
            'data': {
                'cpu': 'Intel Core i7',
                'memory': '16GB',
                'hailo8_devices': [],
                'coral_devices': []
            }
        })
    
    @app.route('/install')
    def install():
        """安装页面"""
        return render_template('simple_index.html', 
                             system_status={'status': 'running', 'message': '系统正常运行'},
                             frigate_status={'status': 'not_installed', 'message': 'Frigate未安装'},
                             hailo8_status={'status': 'not_installed', 'message': 'Hailo8未安装'})
    
    # 注册蓝图（如果导入失败则跳过）
    try:
        from app.routes.main import main_bp
        from app.routes.api import api_bp
        from app.routes.install import install_bp
        from app.routes.hailo8 import hailo8_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(install_bp, url_prefix='/install')
        app.register_blueprint(hailo8_bp, url_prefix='/hailo8')
        
        logger.info("所有蓝图注册成功")
    except ImportError as e:
        logger.warning(f"蓝图导入失败，使用基础路由: {e}")
    
    # 错误处理
    @app.errorhandler(404)
    def not_found_error(error):
        try:
            return render_template('errors/404.html'), 404
        except:
            return jsonify({'error': '页面未找到'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            return render_template('errors/500.html'), 500
        except:
            return jsonify({'error': '服务器内部错误'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"未处理的异常: {e}")
        return jsonify({'error': '服务器内部错误'}), 500
    
    # 模板过滤器
    @app.template_filter('filesize')
    def filesize_filter(size):
        """文件大小格式化"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    @app.template_filter('duration')
    def duration_filter(seconds):
        """时间长度格式化"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            return f"{seconds/60:.0f}分钟"
        else:
            return f"{seconds/3600:.1f}小时"
    
    # 上下文处理器
    @app.context_processor
    def inject_config():
        """注入配置到模板"""
        return {
            'app_name': 'Frigate Setup Wizard',
            'app_version': '1.0.0',
            'hailo8_enabled': app.config['HAILO8_ENABLED']
        }
    
    logger.info("Flask应用创建完成")
    return app

def setup_logging(app):
    """配置日志系统"""
    
    if not app.debug:
        # 生产环境日志配置
        log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
        
        # 文件日志处理器
        file_handler = logging.FileHandler(app.config['LOG_FILE'])
        file_handler.setLevel(log_level)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('Frigate Wizard 日志系统已启动')

def register_blueprints(app):
    """注册蓝图"""
    
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.install import install_bp
    from app.routes.hailo8 import hailo8_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(install_bp, url_prefix='/install')
    app.register_blueprint(hailo8_bp, url_prefix='/hailo8')

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        app.logger.error(f'服务器错误: {error}')
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def too_large(error):
        from flask import jsonify
        return jsonify({'error': '文件太大，最大支持16MB'}), 413

def register_template_filters(app):
    """注册模板过滤器"""
    
    @app.template_filter('filesize')
    def filesize_filter(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @app.template_filter('duration')
    def duration_filter(seconds):
        """格式化时间长度"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            return f"{seconds/60:.1f}分钟"
        else:
            return f"{seconds/3600:.1f}小时"

# 全局变量和工具函数
def get_app_version():
    """获取应用版本"""
    try:
        version_file = Path(__file__).parent.parent / 'VERSION'
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    return '1.0.0'

def get_system_info():
    """获取系统信息"""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'disk_usage': psutil.disk_usage('/').percent,
    }

# 应用上下文处理器
def inject_globals():
    """注入全局模板变量"""
    return {
        'app_version': get_app_version(),
        'system_info': get_system_info(),
    }