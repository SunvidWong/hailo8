#!/usr/bin/env python3
"""
FastAPI 项目 Hailo8 集成示例

展示如何将 Hailo8 TPU 支持集成到 FastAPI 应用中
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_fastapi_project():
    """创建示例 FastAPI 项目"""
    project_path = "/tmp/fastapi_hailo8_app"
    os.makedirs(project_path, exist_ok=True)
    
    # 创建项目结构
    os.makedirs(f"{project_path}/app", exist_ok=True)
    os.makedirs(f"{project_path}/app/api", exist_ok=True)
    os.makedirs(f"{project_path}/app/core", exist_ok=True)
    os.makedirs(f"{project_path}/app/models", exist_ok=True)
    os.makedirs(f"{project_path}/app/static", exist_ok=True)
    os.makedirs(f"{project_path}/app/templates", exist_ok=True)
    
    # 创建主应用文件
    with open(f"{project_path}/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent / "hailo8"))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import logging

from app.api import router as api_router
from app.core.config import settings
from app.core.hailo8_manager import Hailo8Manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="FastAPI Hailo8 应用",
    description="基于 FastAPI 的 Hailo8 TPU 集成应用",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="app/templates")

# 包含 API 路由
app.include_router(api_router, prefix="/api", tags=["api"])

# Hailo8 管理器
hailo8_manager = Hailo8Manager()

@app.on_event("startup")
async def startup_event():
    \"\"\"应用启动事件\"\"\"
    logger.info("启动 FastAPI Hailo8 应用")
    
    # 初始化 Hailo8
    await hailo8_manager.initialize()
    
    if hailo8_manager.is_available():
        logger.info("✓ Hailo8 TPU 已就绪")
    else:
        logger.warning("✗ Hailo8 TPU 不可用")

@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"应用关闭事件\"\"\"
    logger.info("关闭 FastAPI Hailo8 应用")
    await hailo8_manager.cleanup()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    \"\"\"主页\"\"\"
    context = {
        "request": request,
        "title": "FastAPI Hailo8 应用",
        "hailo8_available": hailo8_manager.is_available(),
        "hailo8_enabled": settings.HAILO8_ENABLED
    }
    return templates.TemplateResponse("index.html", context)

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {
        "status": "healthy",
        "hailo8_available": hailo8_manager.is_available(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
""")
    
    # 创建配置文件
    with open(f"{project_path}/app/core/config.py", "w") as f:
        f.write("""import os
from typing import Optional

class Settings:
    \"\"\"应用配置\"\"\"
    
    # 基础配置
    APP_NAME: str = "FastAPI Hailo8 应用"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Hailo8 配置
    HAILO8_ENABLED: bool = os.getenv("HAILO8_ENABLED", "True").lower() == "true"
    HAILO8_AUTO_INSTALL: bool = os.getenv("HAILO8_AUTO_INSTALL", "False").lower() == "true"
    HAILO8_DEVICE_ID: Optional[str] = os.getenv("HAILO8_DEVICE_ID")
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fastapi-hailo8-secret-key")
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
    ]

settings = Settings()
""")
    
    # 创建 Hailo8 管理器
    with open(f"{project_path}/app/core/hailo8_manager.py", "w") as f:
        f.write("""import asyncio
import logging
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hailo8"))

logger = logging.getLogger(__name__)

class Hailo8Manager:
    \"\"\"Hailo8 TPU 管理器\"\"\"
    
    def __init__(self):
        self._available = False
        self._initialized = False
        self._device_info = {}
    
    async def initialize(self) -> bool:
        \"\"\"初始化 Hailo8\"\"\"
        if self._initialized:
            return self._available
        
        try:
            # 导入 Hailo8 支持
            from hailo8_installer import test_hailo8, install_hailo8
            
            # 测试 Hailo8 可用性
            self._available = await asyncio.get_event_loop().run_in_executor(
                None, test_hailo8
            )
            
            if self._available:
                logger.info("Hailo8 TPU 初始化成功")
                await self._get_device_info()
            else:
                logger.warning("Hailo8 TPU 不可用")
            
            self._initialized = True
            return self._available
            
        except ImportError:
            logger.error("Hailo8 支持未集成")
            self._initialized = True
            return False
        except Exception as e:
            logger.error(f"Hailo8 初始化失败: {e}")
            self._initialized = True
            return False
    
    async def _get_device_info(self):
        \"\"\"获取设备信息\"\"\"
        try:
            # 这里可以添加获取设备详细信息的逻辑
            self._device_info = {
                "device_type": "Hailo8",
                "status": "ready",
                "temperature": "normal",
                "utilization": 0
            }
        except Exception as e:
            logger.error(f"获取设备信息失败: {e}")
    
    def is_available(self) -> bool:
        \"\"\"检查 Hailo8 是否可用\"\"\"
        return self._available
    
    def get_device_info(self) -> Dict[str, Any]:
        \"\"\"获取设备信息\"\"\"
        return self._device_info.copy()
    
    async def run_inference(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"运行推理\"\"\"
        if not self._available:
            raise RuntimeError("Hailo8 TPU 不可用")
        
        try:
            # 模拟推理过程
            await asyncio.sleep(0.05)  # 模拟推理时间
            
            result = {
                "status": "success",
                "inference_time": "0.05s",
                "device": "Hailo8 TPU",
                "model": model_data.get("model", "unknown"),
                "input_shape": model_data.get("input_shape", [1, 224, 224, 3]),
                "output_shape": [1, 1000],
                "confidence": 0.95
            }
            
            return result
            
        except Exception as e:
            logger.error(f"推理失败: {e}")
            raise
    
    async def test_performance(self) -> Dict[str, Any]:
        \"\"\"性能测试\"\"\"
        if not self._available:
            raise RuntimeError("Hailo8 TPU 不可用")
        
        try:
            # 模拟性能测试
            test_data = {
                "model": "performance_test",
                "input_shape": [1, 224, 224, 3]
            }
            
            # 运行多次推理测试
            times = []
            for _ in range(10):
                start_time = asyncio.get_event_loop().time()
                await self.run_inference(test_data)
                end_time = asyncio.get_event_loop().time()
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            return {
                "average_inference_time": f"{avg_time:.4f}s",
                "min_inference_time": f"{min_time:.4f}s",
                "max_inference_time": f"{max_time:.4f}s",
                "throughput": f"{1/avg_time:.2f} FPS",
                "test_runs": len(times)
            }
            
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            raise
    
    async def cleanup(self):
        \"\"\"清理资源\"\"\"
        logger.info("清理 Hailo8 资源")
        self._available = False
        self._initialized = False
        self._device_info = {}
""")
    
    # 创建 API 路由
    with open(f"{project_path}/app/api/__init__.py", "w") as f:
        f.write("""from fastapi import APIRouter
from .endpoints import status, inference, performance

router = APIRouter()

# 包含各个端点
router.include_router(status.router, prefix="/status", tags=["status"])
router.include_router(inference.router, prefix="/inference", tags=["inference"])
router.include_router(performance.router, prefix="/performance", tags=["performance"])
""")
    
    # 创建状态端点
    with open(f"{project_path}/app/api/endpoints/status.py", "w") as f:
        f.write("""from fastapi import APIRouter, Depends
from typing import Dict, Any
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "hailo8"))

from app.core.hailo8_manager import Hailo8Manager

router = APIRouter()

# 依赖注入
async def get_hailo8_manager() -> Hailo8Manager:
    # 这里应该从应用状态获取管理器实例
    # 为了简化，创建新实例
    manager = Hailo8Manager()
    await manager.initialize()
    return manager

@router.get("/")
async def get_status(
    hailo8_manager: Hailo8Manager = Depends(get_hailo8_manager)
) -> Dict[str, Any]:
    \"\"\"获取应用状态\"\"\"
    return {
        "status": "ok",
        "hailo8_available": hailo8_manager.is_available(),
        "device_info": hailo8_manager.get_device_info(),
        "message": "Hailo8 TPU 已就绪" if hailo8_manager.is_available() else "Hailo8 TPU 不可用"
    }

@router.get("/hailo8")
async def test_hailo8() -> Dict[str, Any]:
    \"\"\"测试 Hailo8 功能\"\"\"
    try:
        from hailo8_installer import test_hailo8
        
        test_result = test_hailo8()
        
        return {
            "hailo8_test": test_result,
            "message": "Hailo8 测试通过" if test_result else "Hailo8 测试失败"
        }
        
    except ImportError:
        return {
            "error": "Hailo8 支持未集成",
            "message": "请先集成 Hailo8 支持"
        }
    except Exception as e:
        return {
            "error": "测试失败",
            "message": str(e)
        }
""")
    
    # 创建推理端点
    with open(f"{project_path}/app/api/endpoints/inference.py", "w") as f:
        f.write("""from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from app.core.hailo8_manager import Hailo8Manager

router = APIRouter()
logger = logging.getLogger(__name__)

class InferenceRequest(BaseModel):
    \"\"\"推理请求模型\"\"\"
    model: str
    input_data: Optional[Any] = None
    input_shape: Optional[List[int]] = [1, 224, 224, 3]
    parameters: Optional[Dict[str, Any]] = {}

class InferenceResponse(BaseModel):
    \"\"\"推理响应模型\"\"\"
    status: str
    inference_time: str
    device: str
    model: str
    result: Optional[Any] = None

# 依赖注入
async def get_hailo8_manager() -> Hailo8Manager:
    manager = Hailo8Manager()
    await manager.initialize()
    return manager

@router.post("/", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    hailo8_manager: Hailo8Manager = Depends(get_hailo8_manager)
) -> InferenceResponse:
    \"\"\"运行推理\"\"\"
    if not hailo8_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Hailo8 TPU 不可用，请先安装并配置 Hailo8 TPU"
        )
    
    try:
        # 准备推理数据
        model_data = {
            "model": request.model,
            "input_data": request.input_data,
            "input_shape": request.input_shape,
            "parameters": request.parameters
        }
        
        # 运行推理
        result = await hailo8_manager.run_inference(model_data)
        
        return InferenceResponse(
            status=result["status"],
            inference_time=result["inference_time"],
            device=result["device"],
            model=result["model"],
            result=result
        )
        
    except Exception as e:
        logger.error(f"推理失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"推理失败: {str(e)}"
        )

@router.post("/batch")
async def run_batch_inference(
    requests: List[InferenceRequest],
    hailo8_manager: Hailo8Manager = Depends(get_hailo8_manager)
) -> List[InferenceResponse]:
    \"\"\"批量推理\"\"\"
    if not hailo8_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Hailo8 TPU 不可用"
        )
    
    results = []
    
    for request in requests:
        try:
            model_data = {
                "model": request.model,
                "input_data": request.input_data,
                "input_shape": request.input_shape,
                "parameters": request.parameters
            }
            
            result = await hailo8_manager.run_inference(model_data)
            
            results.append(InferenceResponse(
                status=result["status"],
                inference_time=result["inference_time"],
                device=result["device"],
                model=result["model"],
                result=result
            ))
            
        except Exception as e:
            logger.error(f"批量推理中的单个请求失败: {e}")
            results.append(InferenceResponse(
                status="error",
                inference_time="0s",
                device="none",
                model=request.model,
                result={"error": str(e)}
            ))
    
    return results
""")
    
    # 创建性能端点
    with open(f"{project_path}/app/api/endpoints/performance.py", "w") as f:
        f.write("""from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.core.hailo8_manager import Hailo8Manager

router = APIRouter()
logger = logging.getLogger(__name__)

# 依赖注入
async def get_hailo8_manager() -> Hailo8Manager:
    manager = Hailo8Manager()
    await manager.initialize()
    return manager

@router.get("/test")
async def performance_test(
    hailo8_manager: Hailo8Manager = Depends(get_hailo8_manager)
) -> Dict[str, Any]:
    \"\"\"性能测试\"\"\"
    if not hailo8_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Hailo8 TPU 不可用"
        )
    
    try:
        result = await hailo8_manager.test_performance()
        
        return {
            "status": "success",
            "performance_metrics": result,
            "device": "Hailo8 TPU"
        }
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"性能测试失败: {str(e)}"
        )

@router.get("/benchmark")
async def benchmark(
    hailo8_manager: Hailo8Manager = Depends(get_hailo8_manager)
) -> Dict[str, Any]:
    \"\"\"基准测试\"\"\"
    if not hailo8_manager.is_available():
        raise HTTPException(
            status_code=503,
            detail="Hailo8 TPU 不可用"
        )
    
    try:
        # 运行不同模型的基准测试
        models = ["resnet50", "mobilenet_v2", "yolo_v5"]
        results = {}
        
        for model in models:
            model_data = {
                "model": model,
                "input_shape": [1, 224, 224, 3]
            }
            
            # 运行单次推理获取基准
            result = await hailo8_manager.run_inference(model_data)
            results[model] = {
                "inference_time": result["inference_time"],
                "status": result["status"]
            }
        
        return {
            "status": "success",
            "benchmark_results": results,
            "device": "Hailo8 TPU"
        }
        
    except Exception as e:
        logger.error(f"基准测试失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"基准测试失败: {str(e)}"
        )
""")
    
    # 创建端点目录的 __init__.py
    os.makedirs(f"{project_path}/app/api/endpoints", exist_ok=True)
    with open(f"{project_path}/app/api/endpoints/__init__.py", "w") as f:
        f.write("")
    
    # 创建其他 __init__.py 文件
    with open(f"{project_path}/app/__init__.py", "w") as f:
        f.write("")
    
    with open(f"{project_path}/app/core/__init__.py", "w") as f:
        f.write("")
    
    with open(f"{project_path}/app/models/__init__.py", "w") as f:
        f.write("")
    
    # 创建 HTML 模板
    with open(f"{project_path}/app/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/static/style.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <div class="text-center mb-5">
                    <h1 class="display-4">{{ title }}</h1>
                    <p class="lead">基于 FastAPI 的 Hailo8 TPU 集成应用</p>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>系统状态</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="status-item">
                                    <strong>Hailo8 启用:</strong>
                                    <span class="badge {% if hailo8_enabled %}bg-success{% else %}bg-secondary{% endif %}">
                                        {{ "是" if hailo8_enabled else "否" }}
                                    </span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="status-item">
                                    <strong>Hailo8 可用:</strong>
                                    <span class="badge {% if hailo8_available %}bg-success{% else %}bg-danger{% endif %}">
                                        {{ "是" if hailo8_available else "否" }}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        {% if hailo8_available %}
                        <div class="alert alert-success mt-3">
                            <i class="bi bi-check-circle"></i>
                            Hailo8 TPU 已就绪，可以进行高性能推理
                        </div>
                        {% else %}
                        <div class="alert alert-warning mt-3">
                            <i class="bi bi-exclamation-triangle"></i>
                            Hailo8 TPU 不可用，将使用 CPU 模式
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>API 测试</h3>
                    </div>
                    <div class="card-body">
                        <div class="btn-group mb-3" role="group">
                            <button type="button" class="btn btn-primary" onclick="checkStatus()">检查状态</button>
                            <button type="button" class="btn btn-info" onclick="testHailo8()">测试 Hailo8</button>
                            <button type="button" class="btn btn-success" onclick="runInference()">运行推理</button>
                            <button type="button" class="btn btn-warning" onclick="performanceTest()">性能测试</button>
                        </div>
                        
                        <div id="result" class="result-panel" style="display: none;">
                            <h5>API 响应结果:</h5>
                            <pre id="result-content" class="bg-dark text-light p-3 rounded"></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>API 文档</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <a href="/docs" class="btn btn-outline-primary btn-lg w-100 mb-2">
                                    Swagger UI
                                </a>
                            </div>
                            <div class="col-md-4">
                                <a href="/redoc" class="btn btn-outline-info btn-lg w-100 mb-2">
                                    ReDoc
                                </a>
                            </div>
                            <div class="col-md-4">
                                <a href="/health" class="btn btn-outline-success btn-lg w-100 mb-2">
                                    健康检查
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h3>API 端点</h3>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>方法</th>
                                        <th>端点</th>
                                        <th>描述</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><span class="badge bg-success">GET</span></td>
                                        <td><code>/api/status/</code></td>
                                        <td>获取应用状态</td>
                                    </tr>
                                    <tr>
                                        <td><span class="badge bg-success">GET</span></td>
                                        <td><code>/api/status/hailo8</code></td>
                                        <td>测试 Hailo8 功能</td>
                                    </tr>
                                    <tr>
                                        <td><span class="badge bg-primary">POST</span></td>
                                        <td><code>/api/inference/</code></td>
                                        <td>运行推理</td>
                                    </tr>
                                    <tr>
                                        <td><span class="badge bg-primary">POST</span></td>
                                        <td><code>/api/inference/batch</code></td>
                                        <td>批量推理</td>
                                    </tr>
                                    <tr>
                                        <td><span class="badge bg-success">GET</span></td>
                                        <td><code>/api/performance/test</code></td>
                                        <td>性能测试</td>
                                    </tr>
                                    <tr>
                                        <td><span class="badge bg-success">GET</span></td>
                                        <td><code>/api/performance/benchmark</code></td>
                                        <td>基准测试</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>""")
    
    # 创建 CSS 样式
    with open(f"{project_path}/app/static/style.css", "w") as f:
        f.write("""/* FastAPI Hailo8 应用样式 */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.container {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    padding: 30px;
    margin-top: 20px;
    margin-bottom: 20px;
}

.card {
    border: none;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-radius: 10px;
}

.card-header {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border-radius: 10px 10px 0 0 !important;
    border: none;
}

.status-item {
    margin-bottom: 10px;
}

.result-panel {
    margin-top: 20px;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    background: #f8f9fa;
}

.btn-group .btn {
    margin-right: 5px;
}

.table th {
    border-top: none;
    background: #f8f9fa;
}

code {
    background: #e9ecef;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
}

.badge {
    font-size: 0.8em;
}

@media (max-width: 768px) {
    .container {
        margin: 10px;
        padding: 15px;
    }
    
    .btn-group {
        flex-direction: column;
    }
    
    .btn-group .btn {
        margin-bottom: 5px;
        margin-right: 0;
    }
}
""")
    
    # 创建 JavaScript
    with open(f"{project_path}/app/static/app.js", "w") as f:
        f.write("""// FastAPI Hailo8 应用 JavaScript

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
async function checkStatus() {
    try {
        const response = await fetch('/api/status/');
        const data = await response.json();
        showResult(data);
    } catch (error) {
        showError(error);
    }
}

// 测试 Hailo8
async function testHailo8() {
    try {
        const response = await fetch('/api/status/hailo8');
        const data = await response.json();
        showResult(data);
    } catch (error) {
        showError(error);
    }
}

// 运行推理
async function runInference() {
    const testData = {
        model: 'resnet50',
        input_shape: [1, 224, 224, 3],
        parameters: {
            batch_size: 1,
            precision: 'int8',
            optimization_level: 'high'
        }
    };
    
    try {
        const response = await fetch('/api/inference/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        const data = await response.json();
        showResult(data);
    } catch (error) {
        showError(error);
    }
}

// 性能测试
async function performanceTest() {
    try {
        const response = await fetch('/api/performance/test');
        const data = await response.json();
        showResult(data);
    } catch (error) {
        showError(error);
    }
}

// 页面加载完成后自动检查状态
document.addEventListener('DOMContentLoaded', function() {
    console.log('FastAPI Hailo8 应用已加载');
    
    // 自动检查状态
    setTimeout(checkStatus, 1000);
});
""")
    
    # 创建 requirements.txt
    with open(f"{project_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
jinja2>=3.1.0
python-multipart>=0.0.6
aiofiles>=23.0.0
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

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""")
    
    # 创建 docker-compose.yml
    with open(f"{project_path}/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  fastapi-hailo8:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - HAILO8_ENABLED=true
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
      - fastapi-hailo8
    restart: unless-stopped
""")
    
    # 创建 nginx 配置
    with open(f"{project_path}/nginx.conf", "w") as f:
        f.write("""events {
    worker_connections 1024;
}

http {
    upstream fastapi {
        server fastapi-hailo8:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
""")
    
    # 创建启动脚本
    with open(f"{project_path}/start.sh", "w") as f:
        f.write("""#!/bin/bash

# FastAPI Hailo8 应用启动脚本

echo "启动 FastAPI Hailo8 应用..."

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

# 启动应用
echo "启动 FastAPI 服务器..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
""")
    
    # 创建 README
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# FastAPI Hailo8 应用

基于 FastAPI 的 Hailo8 TPU 集成示例应用。

## 功能特性

- FastAPI 高性能框架
- 异步 Hailo8 TPU 支持
- 自动 API 文档生成
- Pydantic 数据验证
- 批量推理支持
- 性能基准测试
- Docker 支持

## 快速开始

### 本地开发

```bash
# 进入项目目录
cd fastapi_hailo8_app

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

# 启动服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
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
- API 文档 (Swagger): http://localhost:8000/docs
- API 文档 (ReDoc): http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API 端点

### 状态检查
- `GET /api/status/` - 应用状态
- `GET /api/status/hailo8` - Hailo8 测试

### 推理接口
- `POST /api/inference/` - 单次推理
- `POST /api/inference/batch` - 批量推理

### 性能测试
- `GET /api/performance/test` - 性能测试
- `GET /api/performance/benchmark` - 基准测试

## 配置

环境变量配置：

- `DEBUG` - 调试模式
- `HOST` - 服务器地址
- `PORT` - 服务器端口
- `HAILO8_ENABLED` - 启用 Hailo8
- `SECRET_KEY` - 应用密钥

## 开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload

# 运行测试
pytest
```

## 生产部署

1. 设置环境变量
2. 使用 gunicorn 或 uvicorn
3. 配置 nginx 反向代理
4. 启用 HTTPS

## API 使用示例

### Python 客户端

```python
import requests

# 检查状态
response = requests.get('http://localhost:8000/api/status/')
print(response.json())

# 运行推理
data = {
    "model": "resnet50",
    "input_shape": [1, 224, 224, 3],
    "parameters": {"batch_size": 1}
}
response = requests.post('http://localhost:8000/api/inference/', json=data)
print(response.json())
```

### curl 示例

```bash
# 检查状态
curl http://localhost:8000/api/status/

# 运行推理
curl -X POST http://localhost:8000/api/inference/ \\
  -H "Content-Type: application/json" \\
  -d '{"model": "resnet50", "input_shape": [1, 224, 224, 3]}'
```
""")
    
    return project_path

def integrate_fastapi_project():
    """集成 FastAPI 项目"""
    print("创建 FastAPI 项目...")
    project_path = create_fastapi_project()
    print(f"FastAPI 项目已创建: {project_path}")
    
    print("\n集成 Hailo8 支持...")
    success = integrate_with_existing_project(
        project_path=project_path,
        project_name="FastAPIHailo8App",
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        log_level="INFO",
        custom_settings={
            "preserve_existing_structure": True,
            "add_to_requirements": True,
            "update_dockerfile": True,
            "create_startup_script": True,
            "fastapi_integration": True
        }
    )
    
    if success:
        print("✓ FastAPI 项目集成成功！")
        print(f"\n项目位置: {project_path}")
        print("\n使用方法:")
        print(f"1. cd {project_path}")
        print("2. chmod +x start.sh && ./start.sh")
        print("3. 访问 http://localhost:8000")
        print("4. API 文档: http://localhost:8000/docs")
        
        print("\nDocker 使用:")
        print("1. docker-compose up -d")
        print("2. 访问 http://localhost")
        
        return True
    else:
        print("✗ FastAPI 项目集成失败")
        return False

def main():
    """主函数"""
    print("FastAPI Hailo8 集成示例")
    print("=" * 40)
    
    try:
        success = integrate_fastapi_project()
        
        if success:
            print("\n✓ 示例创建成功")
            print("现在你可以:")
            print("1. 查看生成的 FastAPI 应用代码")
            print("2. 运行应用测试 Hailo8 集成")
            print("3. 使用异步 API 进行推理")
            print("4. 查看自动生成的 API 文档")
            print("5. 进行性能基准测试")
            print("6. 通过 Docker 部署应用")
        else:
            print("\n✗ 示例创建失败")
            return 1
            
    except Exception as e:
        print(f"\n✗ 执行异常: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())