#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frigate Setup Wizard - 主启动文件
集成Hailo8 TPU支持的Frigate NVR安装向导
"""

import os
import sys
import logging
from pathlib import Path

# 检查Python版本
if sys.version_info < (3, 8):
    print("错误: 需要Python 3.8或更高版本")
    sys.exit(1)

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 创建必要的目录
required_dirs = [
    PROJECT_ROOT / "logs",
    PROJECT_ROOT / "config",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "temp"
]

for dir_path in required_dirs:
    dir_path.mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "wizard.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 导入Flask应用
        from app import create_app
        
        # 创建应用实例
        app = create_app()
        
        # 获取配置
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"启动Frigate Setup Wizard服务器")
        logger.info(f"访问地址: http://{host}:{port}")
        logger.info(f"调试模式: {debug}")
        
        # 启动服务器
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()