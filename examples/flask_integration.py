#!/usr/bin/env python3
"""
Flask 项目 Hailo8 集成示例

展示如何将 Hailo8 TPU 支持集成到 Flask Web 应用中
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_flask_project():
    """创建示例 Flask 项目"""
    project_path = "/tmp/flask_hailo8_app"
    os.makedirs(project_path, exist_ok=True)
    
    # 创建 Flask 应用主文件
    with open(f"{project_path}/app.py", "w") as f:
        f.write("""#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template
import logging
import sys
from pathlib import Path

# 添加 Hailo8 支持路径
sys.path.insert(0, str(Path(__file__).parent / "hailo8"))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hailo8 状态
hailo8_available = False

def initialize_hailo8():
    \"\"\"初始化 Hailo8 支持\"\"\"
    global hailo8_available
    
    try:
        from hailo8_installer import test_hailo8, install_hailo8
        
        if test_hailo8():
            hailo8_available = True
            logger.info("Hailo8 TPU 已就绪")
        else:
            logger.warning("Hailo8 TPU 未安装")
            
    except ImportError:
        logger.info("Hailo8 支持未集成")

@app.route('/')
def index():
    \"\"\"主页\"\"\"
    return render_template('index.html', hailo8_available=hailo8_available)

@app.route('/api/status')
def api_status():
    \"\"\"API 状态检查\"\"\"
    return jsonify({
        'status': 'ok',
        'hailo8_available': hailo8_available,
        'message': 'Hailo8 TPU 已就绪' if hailo8_available else 'Hailo8 TPU 不可用'
    })

@app.route('/api/inference', methods=['POST'])
def api_inference():
    \"\"\"推理 API\"\"\"
    if not hailo8_available:
        return jsonify({
            'error': 'Hailo8 TPU 不可用',
            'message': '请先安装并配置 Hailo8 TPU'
        }), 503
    
    try:
        # 这里添加实际的推理逻辑
        data = request.get_json()
        
        # 模拟推理过程
        result = {
            'status': 'success',
            'message': '推理完成',
            'input_data': data,
            'inference_time': '0.05s',
            'device': 'Hailo8 TPU'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"推理错误: {e}")
        return jsonify({
            'error': '推理失败',
            'message': str(e)
        }), 500

@app.route('/api/test_hailo8')
def api_test_hailo8():
    \"\"\"测试 Hailo8 API\"\"\"
    try:
        from hailo8_installer import test_hailo8
        
        test_result = test_hailo8()
        
        return jsonify({
            'hailo8_test': test_result,
            'message': 'Hailo8 测试通过' if test_result else 'Hailo8 测试失败'
        })
        
    except ImportError:
        return jsonify({
            'error': 'Hailo8 支持未集成',
            'message': '请先集成 Hailo8 支持'
        }), 503
    except Exception as e:
        return jsonify({
            'error': '测试失败',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # 初始化 Hailo8
    initialize_hailo8()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
    
    # 创建模板目录
    os.makedirs(f"{project_path}/templates", exist_ok=True)
    
    # 创建 HTML 模板
    with open(f"{project_path}/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Hailo8 应用</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .status.available {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.unavailable {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Flask Hailo8 TPU 应用</h1>
        
        <div class="status {% if hailo8_available %}available{% else %}unavailable{% endif %}">
            <strong>Hailo8 状态:</strong> 
            {% if hailo8_available %}
                ✓ 已就绪，可以进行 TPU 推理
            {% else %}
                ✗ 不可用，将使用 CPU 模式
            {% endif %}
        </div>
        
        <h2>功能测试</h2>
        
        <button onclick="checkStatus()">检查状态</button>
        <button onclick="testHailo8()">测试 Hailo8</button>
        <button onclick="runInference()">运行推理</button>
        
        <div id="result" class="result" style="display: none;">
            <h3>结果:</h3>
            <pre id="result-content"></pre>
        </div>
        
        <h2>API 端点</h2>
        <ul>
            <li><code>GET /api/status</code> - 检查应用状态</li>
            <li><code>GET /api/test_hailo8</code> - 测试 Hailo8 功能</li>
            <li><code>POST /api/inference</code> - 运行推理</li>
        </ul>
        
        <h2>使用说明</h2>
        <ol>
            <li>确保 Hailo8 TPU 已正确安装和配置</li>
            <li>使用上方按钮测试各项功能</li>
            <li>通过 API 端点进行程序化访问</li>
        </ol>
    </div>

    <script>
        function showResult(data) {
            document.getElementById('result').style.display = 'block';
            document.getElementById('result-content').textContent = JSON.stringify(data, null, 2);
        }
        
        function checkStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => showResult(data))
                .catch(error => showResult({error: error.message}));
        }
        
        function testHailo8() {
            fetch('/api/test_hailo8')
                .then(response => response.json())
                .then(data => showResult(data))
                .catch(error => showResult({error: error.message}));
        }
        
        function runInference() {
            const testData = {
                model: 'example_model',
                input: 'test_input_data',
                parameters: {
                    batch_size: 1,
                    precision: 'int8'
                }
            };
            
            fetch('/api/inference', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testData)
            })
            .then(response => response.json())
            .then(data => showResult(data))
            .catch(error => showResult({error: error.message}));
        }
    </script>
</body>
</html>""")
    
    # 创建 requirements.txt
    with open(f"{project_path}/requirements.txt", "w") as f:
        f.write("""Flask>=2.0.0
gunicorn>=20.1.0
""")
    
    # 创建配置文件
    with open(f"{project_path}/config.py", "w") as f:
        f.write("""# Flask 应用配置
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Hailo8 配置
    HAILO8_ENABLED = os.environ.get('HAILO8_ENABLED', 'True').lower() == 'true'
    HAILO8_AUTO_INSTALL = os.environ.get('HAILO8_AUTO_INSTALL', 'False').lower() == 'true'
    
    # 服务器配置
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
""")
    
    # 创建启动脚本
    with open(f"{project_path}/run.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent / "hailo8"))

from app import app
from config import config

if __name__ == '__main__':
    # 获取配置
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    app_config = config[config_name]
    
    # 应用配置
    app.config.from_object(app_config)
    
    # 启动应用
    app.run(
        host=app_config.HOST,
        port=app_config.PORT,
        debug=app_config.DEBUG
    )
""")
    
    # 创建 Docker 相关文件
    with open(f"{project_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制 Hailo8 集成
COPY hailo8/ ./hailo8/

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "run.py"]
""")
    
    with open(f"{project_path}/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  flask-hailo8:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_CONFIG=production
      - HAILO8_ENABLED=true
    volumes:
      - /dev:/dev
    privileged: true
    restart: unless-stopped
""")
    
    # 创建 README
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# Flask Hailo8 应用

基于 Flask 的 Hailo8 TPU 集成示例应用。

## 功能特性

- Flask Web 框架
- Hailo8 TPU 支持
- RESTful API
- Web 界面
- Docker 支持

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
```

### Docker 运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## API 端点

- `GET /` - Web 界面
- `GET /api/status` - 应用状态
- `GET /api/test_hailo8` - Hailo8 测试
- `POST /api/inference` - 推理接口

## 配置

通过环境变量配置：

- `FLASK_CONFIG` - 配置模式 (development/production)
- `HAILO8_ENABLED` - 启用 Hailo8 支持
- `FLASK_HOST` - 服务器地址
- `FLASK_PORT` - 服务器端口

## 开发

```bash
# 开发模式
export FLASK_CONFIG=development
export FLASK_DEBUG=true
python run.py
```
""")
    
    return project_path

def integrate_flask_project():
    """集成 Flask 项目"""
    print("创建 Flask 项目...")
    project_path = create_flask_project()
    print(f"Flask 项目已创建: {project_path}")
    
    print("\n集成 Hailo8 支持...")
    success = integrate_with_existing_project(
        project_path=project_path,
        project_name="FlaskHailo8App",
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        log_level="INFO",
        custom_settings={
            "preserve_existing_structure": True,
            "add_to_requirements": True,
            "update_dockerfile": True,
            "create_startup_script": True
        }
    )
    
    if success:
        print("✓ Flask 项目集成成功！")
        print(f"\n项目位置: {project_path}")
        print("\n使用方法:")
        print(f"1. cd {project_path}")
        print("2. pip install -r requirements.txt")
        print("3. python run.py")
        print("4. 访问 http://localhost:5000")
        
        print("\nDocker 使用:")
        print("1. docker-compose build")
        print("2. docker-compose up -d")
        
        return True
    else:
        print("✗ Flask 项目集成失败")
        return False

def main():
    """主函数"""
    print("Flask Hailo8 集成示例")
    print("=" * 40)
    
    try:
        success = integrate_flask_project()
        
        if success:
            print("\n✓ 示例创建成功")
            print("现在你可以:")
            print("1. 查看生成的 Flask 应用代码")
            print("2. 运行应用测试 Hailo8 集成")
            print("3. 使用 API 进行推理")
            print("4. 通过 Docker 部署应用")
        else:
            print("\n✗ 示例创建失败")
            return 1
            
    except Exception as e:
        print(f"\n✗ 执行异常: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())