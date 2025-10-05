#!/usr/bin/env python3
"""
Django 项目 Hailo8 集成示例

展示如何将 Hailo8 TPU 支持集成到 Django Web 应用中
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_django_project():
    """创建示例 Django 项目"""
    project_path = "/tmp/django_hailo8_app"
    os.makedirs(project_path, exist_ok=True)
    
    # 创建 Django 项目结构
    os.makedirs(f"{project_path}/hailo8_app", exist_ok=True)
    os.makedirs(f"{project_path}/hailo8_app/api", exist_ok=True)
    os.makedirs(f"{project_path}/hailo8_app/templates", exist_ok=True)
    os.makedirs(f"{project_path}/hailo8_app/static/css", exist_ok=True)
    os.makedirs(f"{project_path}/hailo8_app/static/js", exist_ok=True)
    
    # 创建 manage.py
    with open(f"{project_path}/manage.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent / "hailo8"))

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hailo8_app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
""")
    
    # 创建 settings.py
    with open(f"{project_path}/hailo8_app/settings.py", "w") as f:
        f.write("""import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'hailo8_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hailo8_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'hailo8_app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hailo8_app.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'hailo8_app' / 'static',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Hailo8 配置
HAILO8_ENABLED = os.environ.get('HAILO8_ENABLED', 'True').lower() == 'true'
HAILO8_AUTO_INSTALL = os.environ.get('HAILO8_AUTO_INSTALL', 'False').lower() == 'true'
""")
    
    # 创建 urls.py
    with open(f"{project_path}/hailo8_app/urls.py", "w") as f:
        f.write("""from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/', include('hailo8_app.api.urls')),
]
""")
    
    # 创建 views.py
    with open(f"{project_path}/hailo8_app/views.py", "w") as f:
        f.write("""from django.shortcuts import render
from django.conf import settings
import logging
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent / "hailo8"))

logger = logging.getLogger(__name__)

def get_hailo8_status():
    \"\"\"获取 Hailo8 状态\"\"\"
    try:
        from hailo8_installer import test_hailo8
        return test_hailo8()
    except ImportError:
        logger.warning("Hailo8 支持未集成")
        return False
    except Exception as e:
        logger.error(f"Hailo8 状态检查失败: {e}")
        return False

def index(request):
    \"\"\"主页视图\"\"\"
    context = {
        'hailo8_enabled': settings.HAILO8_ENABLED,
        'hailo8_available': get_hailo8_status(),
        'title': 'Django Hailo8 应用'
    }
    return render(request, 'index.html', context)
""")
    
    # 创建 API urls.py
    with open(f"{project_path}/hailo8_app/api/urls.py", "w") as f:
        f.write("""from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.status_view, name='api_status'),
    path('test_hailo8/', views.test_hailo8_view, name='api_test_hailo8'),
    path('inference/', views.inference_view, name='api_inference'),
]
""")
    
    # 创建 API views.py
    with open(f"{project_path}/hailo8_app/api/views.py", "w") as f:
        f.write("""from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hailo8"))

logger = logging.getLogger(__name__)

@api_view(['GET'])
def status_view(request):
    \"\"\"状态检查 API\"\"\"
    try:
        from hailo8_installer import test_hailo8
        hailo8_available = test_hailo8()
    except ImportError:
        hailo8_available = False
    
    return Response({
        'status': 'ok',
        'hailo8_enabled': settings.HAILO8_ENABLED,
        'hailo8_available': hailo8_available,
        'message': 'Hailo8 TPU 已就绪' if hailo8_available else 'Hailo8 TPU 不可用'
    })

@api_view(['GET'])
def test_hailo8_view(request):
    \"\"\"Hailo8 测试 API\"\"\"
    try:
        from hailo8_installer import test_hailo8
        
        test_result = test_hailo8()
        
        return Response({
            'hailo8_test': test_result,
            'message': 'Hailo8 测试通过' if test_result else 'Hailo8 测试失败'
        })
        
    except ImportError:
        return Response({
            'error': 'Hailo8 支持未集成',
            'message': '请先集成 Hailo8 支持'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Hailo8 测试失败: {e}")
        return Response({
            'error': '测试失败',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def inference_view(request):
    \"\"\"推理 API\"\"\"
    try:
        from hailo8_installer import test_hailo8
        
        if not test_hailo8():
            return Response({
                'error': 'Hailo8 TPU 不可用',
                'message': '请先安装并配置 Hailo8 TPU'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 获取请求数据
        data = request.data
        
        # 模拟推理过程
        result = {
            'status': 'success',
            'message': '推理完成',
            'input_data': data,
            'inference_time': '0.05s',
            'device': 'Hailo8 TPU',
            'model_info': {
                'name': data.get('model', 'default_model'),
                'version': '1.0.0',
                'precision': 'int8'
            }
        }
        
        return Response(result)
        
    except ImportError:
        return Response({
            'error': 'Hailo8 支持未集成',
            'message': '请先集成 Hailo8 支持'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"推理错误: {e}")
        return Response({
            'error': '推理失败',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
""")
    
    # 创建 __init__.py 文件
    with open(f"{project_path}/hailo8_app/__init__.py", "w") as f:
        f.write("")
    
    with open(f"{project_path}/hailo8_app/api/__init__.py", "w") as f:
        f.write("")
    
    # 创建 wsgi.py
    with open(f"{project_path}/hailo8_app/wsgi.py", "w") as f:
        f.write("""import os
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent / "hailo8"))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hailo8_app.settings')

application = get_wsgi_application()
""")
    
    # 创建 HTML 模板
    with open(f"{project_path}/hailo8_app/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <p>基于 Django 的 Hailo8 TPU 集成应用</p>
        </header>
        
        <main>
            <section class="status-section">
                <h2>系统状态</h2>
                <div class="status-card {% if hailo8_available %}available{% else %}unavailable{% endif %}">
                    <h3>Hailo8 TPU 状态</h3>
                    <p class="status-text">
                        {% if hailo8_available %}
                            ✓ 已就绪，可以进行 TPU 推理
                        {% else %}
                            ✗ 不可用，将使用 CPU 模式
                        {% endif %}
                    </p>
                    <div class="status-details">
                        <span>启用状态: {{ hailo8_enabled|yesno:"是,否" }}</span>
                        <span>可用状态: {{ hailo8_available|yesno:"是,否" }}</span>
                    </div>
                </div>
            </section>
            
            <section class="api-section">
                <h2>API 测试</h2>
                <div class="button-group">
                    <button onclick="checkStatus()" class="btn btn-primary">检查状态</button>
                    <button onclick="testHailo8()" class="btn btn-secondary">测试 Hailo8</button>
                    <button onclick="runInference()" class="btn btn-success">运行推理</button>
                </div>
                
                <div id="result" class="result-panel" style="display: none;">
                    <h3>API 响应结果:</h3>
                    <pre id="result-content"></pre>
                </div>
            </section>
            
            <section class="info-section">
                <h2>API 端点</h2>
                <div class="api-list">
                    <div class="api-item">
                        <span class="method get">GET</span>
                        <span class="endpoint">/api/status/</span>
                        <span class="description">检查应用状态</span>
                    </div>
                    <div class="api-item">
                        <span class="method get">GET</span>
                        <span class="endpoint">/api/test_hailo8/</span>
                        <span class="description">测试 Hailo8 功能</span>
                    </div>
                    <div class="api-item">
                        <span class="method post">POST</span>
                        <span class="endpoint">/api/inference/</span>
                        <span class="description">运行推理</span>
                    </div>
                </div>
            </section>
            
            <section class="usage-section">
                <h2>使用说明</h2>
                <ol>
                    <li>确保 Hailo8 TPU 已正确安装和配置</li>
                    <li>使用上方按钮测试各项功能</li>
                    <li>通过 API 端点进行程序化访问</li>
                    <li>查看 Django Admin 管理后台</li>
                </ol>
            </section>
        </main>
        
        <footer>
            <p>&copy; 2024 Django Hailo8 应用. 基于 Django 和 Hailo8 TPU.</p>
        </footer>
    </div>

    <script src="{% static 'js/app.js' %}"></script>
</body>
</html>""")
    
    # 创建 CSS 样式
    with open(f"{project_path}/hailo8_app/static/css/style.css", "w") as f:
        f.write("""/* Django Hailo8 应用样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    margin-top: 20px;
    margin-bottom: 20px;
}

header {
    text-align: center;
    margin-bottom: 40px;
    padding: 30px 0;
    border-bottom: 2px solid #eee;
}

header h1 {
    color: #2c3e50;
    font-size: 2.5em;
    margin-bottom: 10px;
}

header p {
    color: #7f8c8d;
    font-size: 1.2em;
}

section {
    margin-bottom: 40px;
}

section h2 {
    color: #2c3e50;
    margin-bottom: 20px;
    font-size: 1.8em;
    border-left: 4px solid #3498db;
    padding-left: 15px;
}

.status-card {
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-left: 5px solid #e74c3c;
}

.status-card.available {
    border-left-color: #27ae60;
}

.status-card h3 {
    margin-bottom: 15px;
    color: #2c3e50;
}

.status-text {
    font-size: 1.1em;
    margin-bottom: 15px;
}

.status-details {
    display: flex;
    gap: 20px;
    font-size: 0.9em;
    color: #7f8c8d;
}

.button-group {
    display: flex;
    gap: 15px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1em;
    font-weight: 500;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-block;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
    transform: translateY(-2px);
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background: #7f8c8d;
    transform: translateY(-2px);
}

.btn-success {
    background: #27ae60;
    color: white;
}

.btn-success:hover {
    background: #229954;
    transform: translateY(-2px);
}

.result-panel {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    margin-top: 20px;
}

.result-panel h3 {
    margin-bottom: 15px;
    color: #2c3e50;
}

.result-panel pre {
    background: #2c3e50;
    color: #ecf0f1;
    padding: 15px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.9em;
    line-height: 1.4;
}

.api-list {
    display: grid;
    gap: 15px;
}

.api-item {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.method {
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.8em;
    min-width: 50px;
    text-align: center;
}

.method.get {
    background: #27ae60;
    color: white;
}

.method.post {
    background: #e67e22;
    color: white;
}

.endpoint {
    font-family: 'Courier New', monospace;
    background: #ecf0f1;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    min-width: 150px;
}

.description {
    color: #7f8c8d;
}

.usage-section ol {
    padding-left: 20px;
}

.usage-section li {
    margin-bottom: 10px;
    font-size: 1.1em;
}

footer {
    text-align: center;
    padding: 20px 0;
    border-top: 2px solid #eee;
    color: #7f8c8d;
    margin-top: 40px;
}

@media (max-width: 768px) {
    .container {
        margin: 10px;
        padding: 15px;
    }
    
    header h1 {
        font-size: 2em;
    }
    
    .button-group {
        flex-direction: column;
    }
    
    .btn {
        width: 100%;
    }
    
    .api-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    
    .status-details {
        flex-direction: column;
        gap: 5px;
    }
}
""")
    
    # 创建 JavaScript
    with open(f"{project_path}/hailo8_app/static/js/app.js", "w") as f:
        f.write("""// Django Hailo8 应用 JavaScript

// 获取 CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// 显示结果
function showResult(data) {
    const resultDiv = document.getElementById('result');
    const resultContent = document.getElementById('result-content');
    
    resultDiv.style.display = 'block';
    resultContent.textContent = JSON.stringify(data, null, 2);
    
    // 滚动到结果区域
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

// 显示错误
function showError(error) {
    showResult({
        error: true,
        message: error.message || '请求失败',
        details: error
    });
}

// 检查状态
function checkStatus() {
    fetch('/api/status/')
        .then(response => response.json())
        .then(data => showResult(data))
        .catch(error => showError(error));
}

// 测试 Hailo8
function testHailo8() {
    fetch('/api/test_hailo8/')
        .then(response => response.json())
        .then(data => showResult(data))
        .catch(error => showError(error));
}

// 运行推理
function runInference() {
    const testData = {
        model: 'example_model',
        input: 'test_input_data',
        parameters: {
            batch_size: 1,
            precision: 'int8',
            optimization_level: 'high'
        }
    };
    
    fetch('/api/inference/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => showResult(data))
    .catch(error => showError(error));
}

// 页面加载完成后自动检查状态
document.addEventListener('DOMContentLoaded', function() {
    console.log('Django Hailo8 应用已加载');
    
    // 自动检查状态
    setTimeout(checkStatus, 1000);
});
""")
    
    # 创建 requirements.txt
    with open(f"{project_path}/requirements.txt", "w") as f:
        f.write("""Django>=4.2.0
djangorestframework>=3.14.0
gunicorn>=20.1.0
whitenoise>=6.0.0
""")
    
    # 创建 Dockerfile
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

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hailo8_app.wsgi:application"]
""")
    
    # 创建 docker-compose.yml
    with open(f"{project_path}/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  django-hailo8:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - HAILO8_ENABLED=true
      - SECRET_KEY=your-secret-key-here
    volumes:
      - /dev:/dev
    privileged: true
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - django-hailo8
    restart: unless-stopped
""")
    
    # 创建 nginx 配置
    with open(f"{project_path}/nginx.conf", "w") as f:
        f.write("""events {
    worker_connections 1024;
}

http {
    upstream django {
        server django-hailo8:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /static/ {
            proxy_pass http://django;
        }
    }
}
""")
    
    # 创建启动脚本
    with open(f"{project_path}/start.sh", "w") as f:
        f.write("""#!/bin/bash

# Django Hailo8 应用启动脚本

echo "启动 Django Hailo8 应用..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 数据库迁移
echo "执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 创建超级用户（如果不存在）
echo "检查超级用户..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('超级用户已创建: admin/admin123')
else:
    print('超级用户已存在')
"

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 启动开发服务器
echo "启动开发服务器..."
python manage.py runserver 0.0.0.0:8000
""")
    
    # 创建 README
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# Django Hailo8 应用

基于 Django 的 Hailo8 TPU 集成示例应用。

## 功能特性

- Django Web 框架
- Django REST Framework API
- Hailo8 TPU 支持
- 管理后台
- 静态文件服务
- Docker 支持
- Nginx 反向代理

## 快速开始

### 本地开发

```bash
# 克隆项目
cd django_hailo8_app

# 运行启动脚本
chmod +x start.sh
./start.sh
```

### 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务器
python manage.py runserver
```

### Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 访问地址

- 主应用: http://localhost:8000
- API 文档: http://localhost:8000/api/
- 管理后台: http://localhost:8000/admin/

## API 端点

- `GET /api/status/` - 应用状态
- `GET /api/test_hailo8/` - Hailo8 测试
- `POST /api/inference/` - 推理接口

## 配置

环境变量配置：

- `DEBUG` - 调试模式
- `SECRET_KEY` - Django 密钥
- `HAILO8_ENABLED` - 启用 Hailo8
- `DATABASE_URL` - 数据库连接

## 开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python manage.py test

# 启动开发服务器
python manage.py runserver
```

## 生产部署

1. 设置环境变量
2. 配置数据库
3. 收集静态文件
4. 使用 gunicorn + nginx
""")
    
    return project_path

def integrate_django_project():
    """集成 Django 项目"""
    print("创建 Django 项目...")
    project_path = create_django_project()
    print(f"Django 项目已创建: {project_path}")
    
    print("\n集成 Hailo8 支持...")
    success = integrate_with_existing_project(
        project_path=project_path,
        project_name="DjangoHailo8App",
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        log_level="INFO",
        custom_settings={
            "preserve_existing_structure": True,
            "add_to_requirements": True,
            "update_dockerfile": True,
            "create_startup_script": True,
            "django_integration": True
        }
    )
    
    if success:
        print("✓ Django 项目集成成功！")
        print(f"\n项目位置: {project_path}")
        print("\n使用方法:")
        print(f"1. cd {project_path}")
        print("2. chmod +x start.sh && ./start.sh")
        print("3. 访问 http://localhost:8000")
        print("4. 管理后台: http://localhost:8000/admin/ (admin/admin123)")
        
        print("\nDocker 使用:")
        print("1. docker-compose up -d")
        print("2. 访问 http://localhost")
        
        return True
    else:
        print("✗ Django 项目集成失败")
        return False

def main():
    """主函数"""
    print("Django Hailo8 集成示例")
    print("=" * 40)
    
    try:
        success = integrate_django_project()
        
        if success:
            print("\n✓ 示例创建成功")
            print("现在你可以:")
            print("1. 查看生成的 Django 应用代码")
            print("2. 运行应用测试 Hailo8 集成")
            print("3. 使用 REST API 进行推理")
            print("4. 访问 Django 管理后台")
            print("5. 通过 Docker 部署应用")
        else:
            print("\n✗ 示例创建失败")
            return 1
            
    except Exception as e:
        print(f"\n✗ 执行异常: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())