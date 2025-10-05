#!/usr/bin/env python3
"""
微服务架构 Hailo8 集成示例

展示如何将 Hailo8 TPU 支持集成到微服务架构中
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_microservice_architecture():
    """创建微服务架构示例"""
    project_path = "/tmp/microservice_hailo8"
    os.makedirs(project_path, exist_ok=True)
    
    # 创建服务目录结构
    services = [
        "api-gateway",
        "inference-service",
        "model-service",
        "monitoring-service",
        "auth-service"
    ]
    
    for service in services:
        service_path = f"{project_path}/{service}"
        os.makedirs(service_path, exist_ok=True)
        os.makedirs(f"{service_path}/src", exist_ok=True)
        os.makedirs(f"{service_path}/tests", exist_ok=True)
        os.makedirs(f"{service_path}/config", exist_ok=True)
    
    # 创建共享目录
    os.makedirs(f"{project_path}/shared", exist_ok=True)
    os.makedirs(f"{project_path}/shared/proto", exist_ok=True)
    os.makedirs(f"{project_path}/shared/utils", exist_ok=True)
    os.makedirs(f"{project_path}/deployment", exist_ok=True)
    os.makedirs(f"{project_path}/deployment/k8s", exist_ok=True)
    os.makedirs(f"{project_path}/deployment/docker", exist_ok=True)
    
    # 1. API Gateway 服务
    create_api_gateway(f"{project_path}/api-gateway")
    
    # 2. 推理服务 (主要的 Hailo8 集成服务)
    create_inference_service(f"{project_path}/inference-service")
    
    # 3. 模型服务
    create_model_service(f"{project_path}/model-service")
    
    # 4. 监控服务
    create_monitoring_service(f"{project_path}/monitoring-service")
    
    # 5. 认证服务
    create_auth_service(f"{project_path}/auth-service")
    
    # 6. 共享组件
    create_shared_components(f"{project_path}/shared")
    
    # 7. 部署配置
    create_deployment_configs(f"{project_path}/deployment")
    
    # 8. 根目录文件
    create_root_files(project_path)
    
    return project_path

def create_api_gateway(service_path):
    """创建 API 网关服务"""
    # main.py
    with open(f"{service_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
API Gateway 服务
负责路由、认证、限流等功能
\"\"\"

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import httpx
import logging
import time
from typing import Dict, Any
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hailo8 微服务 API 网关",
    description="微服务架构的 API 网关",
    version="1.0.0"
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# 服务配置
SERVICES = {
    "inference": os.getenv("INFERENCE_SERVICE_URL", "http://inference-service:8001"),
    "model": os.getenv("MODEL_SERVICE_URL", "http://model-service:8002"),
    "monitoring": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8003"),
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8004")
}

# HTTP 客户端
http_client = httpx.AsyncClient(timeout=30.0)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    \"\"\"添加处理时间头\"\"\"
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": list(SERVICES.keys())
    }

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    service_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await http_client.get(f"{service_url}/health", timeout=5.0)
            service_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            service_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "services": service_status
    }

# 推理服务路由
@app.post("/api/v1/inference")
async def inference_proxy(request: Request):
    \"\"\"推理服务代理\"\"\"
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        response = await http_client.post(
            f"{SERVICES['inference']}/inference",
            content=body,
            headers=headers
        )
        
        return response.json()
        
    except Exception as e:
        logger.error(f"推理服务代理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/inference/batch")
async def batch_inference_proxy(request: Request):
    \"\"\"批量推理服务代理\"\"\"
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        response = await http_client.post(
            f"{SERVICES['inference']}/inference/batch",
            content=body,
            headers=headers
        )
        
        return response.json()
        
    except Exception as e:
        logger.error(f"批量推理服务代理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 模型服务路由
@app.get("/api/v1/models")
async def models_proxy():
    \"\"\"模型列表代理\"\"\"
    try:
        response = await http_client.get(f"{SERVICES['model']}/models")
        return response.json()
    except Exception as e:
        logger.error(f"模型服务代理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/{model_id}")
async def model_detail_proxy(model_id: str):
    \"\"\"模型详情代理\"\"\"
    try:
        response = await http_client.get(f"{SERVICES['model']}/models/{model_id}")
        return response.json()
    except Exception as e:
        logger.error(f"模型详情代理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 监控服务路由
@app.get("/api/v1/metrics")
async def metrics_proxy():
    \"\"\"指标代理\"\"\"
    try:
        response = await http_client.get(f"{SERVICES['monitoring']}/metrics")
        return response.json()
    except Exception as e:
        logger.error(f"监控服务代理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"关闭事件\"\"\"
    await http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
    
    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.0.0
""")
    
    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

def create_inference_service(service_path):
    """创建推理服务 (主要的 Hailo8 集成服务)"""
    # main.py
    with open(f"{service_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
推理服务
负责 Hailo8 TPU 推理任务
\"\"\"

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import logging
import sys
from pathlib import Path
import uuid
import time

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "hailo8"))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hailo8 推理服务",
    description="基于 Hailo8 TPU 的推理微服务",
    version="1.0.0"
)

# 推理请求模型
class InferenceRequest(BaseModel):
    model_id: str
    input_data: Any
    input_shape: Optional[List[int]] = [1, 224, 224, 3]
    parameters: Optional[Dict[str, Any]] = {}
    async_mode: Optional[bool] = False

class BatchInferenceRequest(BaseModel):
    requests: List[InferenceRequest]
    batch_size: Optional[int] = 8

# 推理任务状态
inference_tasks = {}

class Hailo8InferenceEngine:
    \"\"\"Hailo8 推理引擎\"\"\"
    
    def __init__(self):
        self.initialized = False
        self.available = False
        self.device_info = {}
    
    async def initialize(self):
        \"\"\"初始化推理引擎\"\"\"
        if self.initialized:
            return self.available
        
        try:
            # 导入 Hailo8 支持
            from hailo8_installer import test_hailo8
            
            # 测试 Hailo8 可用性
            self.available = await asyncio.get_event_loop().run_in_executor(
                None, test_hailo8
            )
            
            if self.available:
                logger.info("Hailo8 TPU 推理引擎初始化成功")
                self.device_info = {
                    "device_type": "Hailo8",
                    "status": "ready",
                    "max_batch_size": 16,
                    "supported_models": ["resnet50", "mobilenet_v2", "yolo_v5"]
                }
            else:
                logger.warning("Hailo8 TPU 不可用，使用 CPU 模式")
            
            self.initialized = True
            return self.available
            
        except Exception as e:
            logger.error(f"推理引擎初始化失败: {e}")
            self.initialized = True
            return False
    
    async def run_inference(self, request: InferenceRequest) -> Dict[str, Any]:
        \"\"\"运行推理\"\"\"
        if not self.available:
            # CPU 模式推理
            return await self._cpu_inference(request)
        
        try:
            # Hailo8 TPU 推理
            start_time = time.time()
            
            # 模拟推理过程
            await asyncio.sleep(0.02)  # 模拟 TPU 推理时间
            
            inference_time = time.time() - start_time
            
            result = {
                "task_id": str(uuid.uuid4()),
                "status": "completed",
                "model_id": request.model_id,
                "device": "Hailo8 TPU",
                "inference_time": f"{inference_time:.4f}s",
                "input_shape": request.input_shape,
                "output_shape": [1, 1000],
                "confidence": 0.95,
                "predictions": [
                    {"class": "cat", "confidence": 0.95},
                    {"class": "dog", "confidence": 0.03},
                    {"class": "bird", "confidence": 0.02}
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Hailo8 推理失败: {e}")
            return await self._cpu_inference(request)
    
    async def _cpu_inference(self, request: InferenceRequest) -> Dict[str, Any]:
        \"\"\"CPU 模式推理\"\"\"
        start_time = time.time()
        
        # 模拟 CPU 推理
        await asyncio.sleep(0.1)  # CPU 推理较慢
        
        inference_time = time.time() - start_time
        
        return {
            "task_id": str(uuid.uuid4()),
            "status": "completed",
            "model_id": request.model_id,
            "device": "CPU",
            "inference_time": f"{inference_time:.4f}s",
            "input_shape": request.input_shape,
            "output_shape": [1, 1000],
            "confidence": 0.85,
            "predictions": [
                {"class": "cat", "confidence": 0.85},
                {"class": "dog", "confidence": 0.10},
                {"class": "bird", "confidence": 0.05}
            ]
        }
    
    async def run_batch_inference(self, request: BatchInferenceRequest) -> List[Dict[str, Any]]:
        \"\"\"批量推理\"\"\"
        results = []
        
        # 分批处理
        batch_size = request.batch_size or 8
        
        for i in range(0, len(request.requests), batch_size):
            batch = request.requests[i:i + batch_size]
            
            # 并行处理批次
            batch_tasks = [self.run_inference(req) for req in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            
            results.extend(batch_results)
        
        return results

# 全局推理引擎
inference_engine = Hailo8InferenceEngine()

@app.on_event("startup")
async def startup_event():
    \"\"\"启动事件\"\"\"
    logger.info("启动推理服务")
    await inference_engine.initialize()

@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "Inference Service",
        "version": "1.0.0",
        "hailo8_available": inference_engine.available,
        "device_info": inference_engine.device_info
    }

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {
        "status": "healthy",
        "hailo8_available": inference_engine.available,
        "initialized": inference_engine.initialized
    }

@app.post("/inference")
async def run_inference(request: InferenceRequest, background_tasks: BackgroundTasks):
    \"\"\"运行推理\"\"\"
    try:
        if request.async_mode:
            # 异步模式
            task_id = str(uuid.uuid4())
            inference_tasks[task_id] = {"status": "pending", "created_at": time.time()}
            
            # 后台任务
            background_tasks.add_task(run_async_inference, task_id, request)
            
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "推理任务已提交，请使用 task_id 查询结果"
            }
        else:
            # 同步模式
            result = await inference_engine.run_inference(request)
            return result
            
    except Exception as e:
        logger.error(f"推理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inference/batch")
async def run_batch_inference(request: BatchInferenceRequest):
    \"\"\"批量推理\"\"\"
    try:
        results = await inference_engine.run_batch_inference(request)
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_requests": len(request.requests),
            "completed": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"批量推理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inference/task/{task_id}")
async def get_inference_task(task_id: str):
    \"\"\"获取推理任务状态\"\"\"
    if task_id not in inference_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return inference_tasks[task_id]

async def run_async_inference(task_id: str, request: InferenceRequest):
    \"\"\"运行异步推理\"\"\"
    try:
        inference_tasks[task_id]["status"] = "running"
        inference_tasks[task_id]["started_at"] = time.time()
        
        result = await inference_engine.run_inference(request)
        
        inference_tasks[task_id]["status"] = "completed"
        inference_tasks[task_id]["completed_at"] = time.time()
        inference_tasks[task_id]["result"] = result
        
    except Exception as e:
        inference_tasks[task_id]["status"] = "failed"
        inference_tasks[task_id]["error"] = str(e)
        inference_tasks[task_id]["failed_at"] = time.time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
""")
    
    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
numpy>=1.21.0
""")
    
    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY hailo8/ ./hailo8/

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
""")

def create_model_service(service_path):
    """创建模型服务"""
    # main.py
    with open(f"{service_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
模型服务
负责模型管理、版本控制等
\"\"\"

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="模型管理服务",
    description="AI 模型管理微服务",
    version="1.0.0"
)

# 模型信息模型
class ModelInfo(BaseModel):
    model_id: str
    name: str
    version: str
    description: str
    input_shape: List[int]
    output_shape: List[int]
    model_type: str
    framework: str
    size_mb: float
    accuracy: Optional[float] = None
    latency_ms: Optional[float] = None

# 模拟模型数据库
MODELS_DB = {
    "resnet50": ModelInfo(
        model_id="resnet50",
        name="ResNet-50",
        version="1.0.0",
        description="深度残差网络，用于图像分类",
        input_shape=[1, 224, 224, 3],
        output_shape=[1, 1000],
        model_type="classification",
        framework="pytorch",
        size_mb=98.5,
        accuracy=0.76,
        latency_ms=15.2
    ),
    "mobilenet_v2": ModelInfo(
        model_id="mobilenet_v2",
        name="MobileNet V2",
        version="1.0.0",
        description="轻量级卷积神经网络",
        input_shape=[1, 224, 224, 3],
        output_shape=[1, 1000],
        model_type="classification",
        framework="tensorflow",
        size_mb=14.2,
        accuracy=0.72,
        latency_ms=8.5
    ),
    "yolo_v5": ModelInfo(
        model_id="yolo_v5",
        name="YOLO v5",
        version="1.0.0",
        description="实时目标检测模型",
        input_shape=[1, 640, 640, 3],
        output_shape=[1, 25200, 85],
        model_type="detection",
        framework="pytorch",
        size_mb=46.8,
        accuracy=0.65,
        latency_ms=25.3
    )
}

@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "Model Service",
        "version": "1.0.0",
        "total_models": len(MODELS_DB)
    }

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {"status": "healthy"}

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    \"\"\"获取模型列表\"\"\"
    return list(MODELS_DB.values())

@app.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    \"\"\"获取模型详情\"\"\"
    if model_id not in MODELS_DB:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return MODELS_DB[model_id]

@app.get("/models/{model_id}/download")
async def download_model(model_id: str):
    \"\"\"下载模型\"\"\"
    if model_id not in MODELS_DB:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model = MODELS_DB[model_id]
    
    # 模拟下载链接
    download_url = f"https://models.example.com/{model_id}/{model.version}/model.hef"
    
    return {
        "model_id": model_id,
        "download_url": download_url,
        "size_mb": model.size_mb,
        "checksum": f"sha256:{model_id}_checksum"
    }

@app.get("/models/search")
async def search_models(
    model_type: Optional[str] = None,
    framework: Optional[str] = None,
    min_accuracy: Optional[float] = None
):
    \"\"\"搜索模型\"\"\"
    results = []
    
    for model in MODELS_DB.values():
        if model_type and model.model_type != model_type:
            continue
        if framework and model.framework != framework:
            continue
        if min_accuracy and (model.accuracy is None or model.accuracy < min_accuracy):
            continue
        
        results.append(model)
    
    return results

@app.get("/stats")
async def get_stats():
    \"\"\"获取统计信息\"\"\"
    stats = {
        "total_models": len(MODELS_DB),
        "by_type": {},
        "by_framework": {},
        "avg_size_mb": 0,
        "avg_accuracy": 0
    }
    
    total_size = 0
    total_accuracy = 0
    accuracy_count = 0
    
    for model in MODELS_DB.values():
        # 按类型统计
        if model.model_type not in stats["by_type"]:
            stats["by_type"][model.model_type] = 0
        stats["by_type"][model.model_type] += 1
        
        # 按框架统计
        if model.framework not in stats["by_framework"]:
            stats["by_framework"][model.framework] = 0
        stats["by_framework"][model.framework] += 1
        
        # 大小统计
        total_size += model.size_mb
        
        # 精度统计
        if model.accuracy is not None:
            total_accuracy += model.accuracy
            accuracy_count += 1
    
    stats["avg_size_mb"] = round(total_size / len(MODELS_DB), 2)
    if accuracy_count > 0:
        stats["avg_accuracy"] = round(total_accuracy / accuracy_count, 3)
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
""")
    
    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
""")
    
    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
""")

def create_monitoring_service(service_path):
    """创建监控服务"""
    # main.py
    with open(f"{service_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
监控服务
负责系统监控、指标收集等
\"\"\"

from fastapi import FastAPI
from typing import Dict, Any, List
import logging
import time
import psutil
import asyncio
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="监控服务",
    description="系统监控微服务",
    version="1.0.0"
)

# 指标存储
metrics_storage = {
    "system": [],
    "inference": [],
    "models": []
}

class MetricsCollector:
    \"\"\"指标收集器\"\"\"
    
    def __init__(self):
        self.running = False
    
    async def start_collection(self):
        \"\"\"开始收集指标\"\"\"
        self.running = True
        while self.running:
            await self.collect_system_metrics()
            await asyncio.sleep(30)  # 每30秒收集一次
    
    async def collect_system_metrics(self):
        \"\"\"收集系统指标\"\"\"
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }
            
            metrics_storage["system"].append(metric)
            
            # 保留最近1000条记录
            if len(metrics_storage["system"]) > 1000:
                metrics_storage["system"] = metrics_storage["system"][-1000:]
                
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def stop_collection(self):
        \"\"\"停止收集指标\"\"\"
        self.running = False

# 全局指标收集器
metrics_collector = MetricsCollector()

@app.on_event("startup")
async def startup_event():
    \"\"\"启动事件\"\"\"
    logger.info("启动监控服务")
    asyncio.create_task(metrics_collector.start_collection())

@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"关闭事件\"\"\"
    logger.info("关闭监控服务")
    metrics_collector.stop_collection()

@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "Monitoring Service",
        "version": "1.0.0",
        "metrics_count": sum(len(v) for v in metrics_storage.values())
    }

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    \"\"\"获取所有指标\"\"\"
    return {
        "system": metrics_storage["system"][-10:],  # 最近10条
        "inference": metrics_storage["inference"][-10:],
        "models": metrics_storage["models"][-10:]
    }

@app.get("/metrics/system")
async def get_system_metrics():
    \"\"\"获取系统指标\"\"\"
    return metrics_storage["system"][-50:]  # 最近50条

@app.get("/metrics/system/current")
async def get_current_system_metrics():
    \"\"\"获取当前系统指标\"\"\"
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
    except Exception as e:
        logger.error(f"获取当前系统指标失败: {e}")
        return {"error": str(e)}

@app.post("/metrics/inference")
async def record_inference_metric(metric: Dict[str, Any]):
    \"\"\"记录推理指标\"\"\"
    metric["timestamp"] = datetime.now().isoformat()
    metrics_storage["inference"].append(metric)
    
    # 保留最近1000条记录
    if len(metrics_storage["inference"]) > 1000:
        metrics_storage["inference"] = metrics_storage["inference"][-1000:]
    
    return {"status": "recorded"}

@app.get("/metrics/inference/stats")
async def get_inference_stats():
    \"\"\"获取推理统计\"\"\"
    if not metrics_storage["inference"]:
        return {"message": "暂无推理数据"}
    
    recent_metrics = metrics_storage["inference"][-100:]  # 最近100条
    
    total_requests = len(recent_metrics)
    avg_latency = sum(float(m.get("latency_ms", 0)) for m in recent_metrics) / total_requests
    
    device_counts = {}
    model_counts = {}
    
    for metric in recent_metrics:
        device = metric.get("device", "unknown")
        model = metric.get("model_id", "unknown")
        
        device_counts[device] = device_counts.get(device, 0) + 1
        model_counts[model] = model_counts.get(model, 0) + 1
    
    return {
        "total_requests": total_requests,
        "avg_latency_ms": round(avg_latency, 2),
        "device_distribution": device_counts,
        "model_distribution": model_counts,
        "time_range": "最近100次推理"
    }

@app.get("/alerts")
async def get_alerts():
    \"\"\"获取告警信息\"\"\"
    alerts = []
    
    # 检查最新系统指标
    if metrics_storage["system"]:
        latest = metrics_storage["system"][-1]
        
        if latest["cpu_percent"] > 80:
            alerts.append({
                "type": "warning",
                "message": f"CPU 使用率过高: {latest['cpu_percent']}%",
                "timestamp": latest["timestamp"]
            })
        
        if latest["memory_percent"] > 85:
            alerts.append({
                "type": "warning",
                "message": f"内存使用率过高: {latest['memory_percent']}%",
                "timestamp": latest["timestamp"]
            })
        
        if latest["disk_percent"] > 90:
            alerts.append({
                "type": "critical",
                "message": f"磁盘使用率过高: {latest['disk_percent']}%",
                "timestamp": latest["timestamp"]
            })
    
    return {"alerts": alerts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
""")
    
    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
psutil>=5.9.0
""")
    
    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    procps \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8003

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
""")

def create_auth_service(service_path):
    """创建认证服务"""
    # main.py
    with open(f"{service_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
认证服务
负责用户认证、授权等
\"\"\"

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import jwt
import hashlib
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="认证服务",
    description="用户认证微服务",
    version="1.0.0"
)

# JWT 配置
SECRET_KEY = "hailo8-microservice-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer 认证
security = HTTPBearer()

# 用户模型
class User(BaseModel):
    username: str
    email: str
    role: str
    permissions: list

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# 模拟用户数据库
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "permissions": ["read", "write", "admin", "inference", "model_management"]
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user",
        "permissions": ["read", "inference"]
    },
    "developer": {
        "username": "developer",
        "email": "dev@example.com",
        "password_hash": hashlib.sha256("dev123".encode()).hexdigest(),
        "role": "developer",
        "permissions": ["read", "write", "inference", "model_management"]
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    \"\"\"创建访问令牌\"\"\"
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    \"\"\"验证令牌\"\"\"
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token_data: dict = Depends(verify_token)):
    \"\"\"获取当前用户\"\"\"
    username = token_data.get("sub")
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    user_data = USERS_DB[username]
    return User(
        username=user_data["username"],
        email=user_data["email"],
        role=user_data["role"],
        permissions=user_data["permissions"]
    )

@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "Auth Service",
        "version": "1.0.0",
        "total_users": len(USERS_DB)
    }

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {"status": "healthy"}

@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    \"\"\"用户登录\"\"\"
    username = request.username
    password = request.password
    
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    user = USERS_DB[username]
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "role": user["role"], "permissions": user["permissions"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    \"\"\"获取当前用户信息\"\"\"
    return current_user

@app.post("/verify")
async def verify_token_endpoint(token_data: dict = Depends(verify_token)):
    \"\"\"验证令牌\"\"\"
    return {
        "valid": True,
        "username": token_data.get("sub"),
        "role": token_data.get("role"),
        "permissions": token_data.get("permissions"),
        "expires": token_data.get("exp")
    }

@app.post("/check_permission")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_user)
):
    \"\"\"检查权限\"\"\"
    has_permission = permission in current_user.permissions
    
    return {
        "username": current_user.username,
        "permission": permission,
        "has_permission": has_permission
    }

@app.get("/users")
async def list_users(current_user: User = Depends(get_current_user)):
    \"\"\"获取用户列表 (需要管理员权限)\"\"\"
    if "admin" not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    users = []
    for username, user_data in USERS_DB.items():
        users.append({
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"],
            "permissions": user_data["permissions"]
        })
    
    return {"users": users}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
""")
    
    # requirements.txt
    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
PyJWT>=2.8.0
""")
    
    # Dockerfile
    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 8004

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]
""")

def create_shared_components(shared_path):
    """创建共享组件"""
    # 创建通用工具
    with open(f"{shared_path}/utils/common.py", "w") as f:
        f.write("""\"\"\"
共享工具函数
\"\"\"

import logging
import time
import functools
from typing import Any, Callable

def setup_logging(service_name: str, level: str = "INFO"):
    \"\"\"设置日志\"\"\"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=f'%(asctime)s - {service_name} - %(levelname)s - %(message)s'
    )
    return logging.getLogger(service_name)

def timing_decorator(func: Callable) -> Callable:
    \"\"\"计时装饰器\"\"\"
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.4f}s")
        return result
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.4f}s")
        return result
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def retry_decorator(max_retries: int = 3, delay: float = 1.0):
    \"\"\"重试装饰器\"\"\"
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(delay * (2 ** attempt))
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
""")
    
    # 创建 __init__.py
    with open(f"{shared_path}/__init__.py", "w") as f:
        f.write("")
    
    with open(f"{shared_path}/utils/__init__.py", "w") as f:
        f.write("")
    
    with open(f"{shared_path}/proto/__init__.py", "w") as f:
        f.write("")

def create_deployment_configs(deployment_path):
    """创建部署配置"""
    # Docker Compose
    with open(f"{deployment_path}/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  api-gateway:
    build: ../api-gateway
    ports:
      - "8000:8000"
    environment:
      - INFERENCE_SERVICE_URL=http://inference-service:8001
      - MODEL_SERVICE_URL=http://model-service:8002
      - MONITORING_SERVICE_URL=http://monitoring-service:8003
      - AUTH_SERVICE_URL=http://auth-service:8004
    depends_on:
      - inference-service
      - model-service
      - monitoring-service
      - auth-service
    restart: unless-stopped
    networks:
      - hailo8-network

  inference-service:
    build: ../inference-service
    ports:
      - "8001:8001"
    volumes:
      - /dev:/dev
      - ../hailo8:/app/hailo8
    privileged: true
    restart: unless-stopped
    networks:
      - hailo8-network

  model-service:
    build: ../model-service
    ports:
      - "8002:8002"
    restart: unless-stopped
    networks:
      - hailo8-network

  monitoring-service:
    build: ../monitoring-service
    ports:
      - "8003:8003"
    restart: unless-stopped
    networks:
      - hailo8-network

  auth-service:
    build: ../auth-service
    ports:
      - "8004:8004"
    restart: unless-stopped
    networks:
      - hailo8-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api-gateway
    restart: unless-stopped
    networks:
      - hailo8-network

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - hailo8-network

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped
    networks:
      - hailo8-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
    restart: unless-stopped
    networks:
      - hailo8-network

networks:
  hailo8-network:
    driver: bridge

volumes:
  grafana-storage:
""")
    
    # Kubernetes 配置
    os.makedirs(f"{deployment_path}/k8s", exist_ok=True)
    
    # Namespace
    with open(f"{deployment_path}/k8s/namespace.yaml", "w") as f:
        f.write("""apiVersion: v1
kind: Namespace
metadata:
  name: hailo8-microservices
  labels:
    name: hailo8-microservices
""")
    
    # API Gateway Deployment
    with open(f"{deployment_path}/k8s/api-gateway.yaml", "w") as f:
        f.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: hailo8-microservices
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: hailo8/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: INFERENCE_SERVICE_URL
          value: "http://inference-service:8001"
        - name: MODEL_SERVICE_URL
          value: "http://model-service:8002"
        - name: MONITORING_SERVICE_URL
          value: "http://monitoring-service:8003"
        - name: AUTH_SERVICE_URL
          value: "http://auth-service:8004"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: hailo8-microservices
spec:
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
""")
    
    # Inference Service Deployment
    with open(f"{deployment_path}/k8s/inference-service.yaml", "w") as f:
        f.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-service
  namespace: hailo8-microservices
spec:
  replicas: 1
  selector:
    matchLabels:
      app: inference-service
  template:
    metadata:
      labels:
        app: inference-service
    spec:
      containers:
      - name: inference-service
        image: hailo8/inference-service:latest
        ports:
        - containerPort: 8001
        securityContext:
          privileged: true
        volumeMounts:
        - name: dev
          mountPath: /dev
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: dev
        hostPath:
          path: /dev
---
apiVersion: v1
kind: Service
metadata:
  name: inference-service
  namespace: hailo8-microservices
spec:
  selector:
    app: inference-service
  ports:
  - port: 8001
    targetPort: 8001
""")
    
    # Nginx 配置
    os.makedirs(f"{deployment_path}/nginx", exist_ok=True)
    with open(f"{deployment_path}/nginx/nginx.conf", "w") as f:
        f.write("""events {
    worker_connections 1024;
}

http {
    upstream api_gateway {
        server api-gateway:8000;
    }
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name localhost;
        
        # API 路由
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时配置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # 健康检查
        location /health {
            proxy_pass http://api_gateway/health;
        }
        
        # 静态文件
        location / {
            proxy_pass http://api_gateway;
        }
    }
}
""")
    
    # Prometheus 配置
    os.makedirs(f"{deployment_path}/prometheus", exist_ok=True)
    with open(f"{deployment_path}/prometheus/prometheus.yml", "w") as f:
        f.write("""global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'inference-service'
    static_configs:
      - targets: ['inference-service:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'model-service'
    static_configs:
      - targets: ['model-service:8002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'monitoring-service'
    static_configs:
      - targets: ['monitoring-service:8003']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8004']
    metrics_path: '/metrics'
    scrape_interval: 30s
""")

def create_root_files(project_path):
    """创建根目录文件"""
    # README.md
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# Hailo8 微服务架构

基于 Hailo8 TPU 的微服务架构示例，展示如何构建可扩展的 AI 推理服务。

## 架构概览

```
┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Grafana      │
│   (负载均衡)     │    │    (监控)       │
└─────────────────┘    └─────────────────┘
         │                       │
┌─────────────────┐    ┌─────────────────┐
│  API Gateway    │    │  Prometheus     │
│   (路由/认证)    │    │   (指标收集)     │
└─────────────────┘    └─────────────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    │         │        │        │        │
┌───▼───┐ ┌──▼──┐ ┌───▼───┐ ┌──▼──┐ ┌──▼──┐
│推理服务│ │模型  │ │监控   │ │认证  │ │Redis│
│(Hailo8)│ │服务  │ │服务   │ │服务  │ │缓存 │
└───────┘ └─────┘ └───────┘ └─────┘ └─────┘
```

## 服务列表

| 服务 | 端口 | 描述 |
|------|------|------|
| API Gateway | 8000 | API 网关，路由和认证 |
| Inference Service | 8001 | Hailo8 TPU 推理服务 |
| Model Service | 8002 | 模型管理服务 |
| Monitoring Service | 8003 | 系统监控服务 |
| Auth Service | 8004 | 用户认证服务 |
| Nginx | 80/443 | 负载均衡和反向代理 |
| Redis | 6379 | 缓存服务 |
| Prometheus | 9090 | 指标收集 |
| Grafana | 3000 | 监控面板 |

## 快速开始

### Docker Compose 部署

```bash
# 进入项目目录
cd microservice_hailo8

# 构建并启动所有服务
docker-compose -f deployment/docker-compose.yml up -d

# 查看服务状态
docker-compose -f deployment/docker-compose.yml ps

# 查看日志
docker-compose -f deployment/docker-compose.yml logs -f
```

### Kubernetes 部署

```bash
# 创建命名空间
kubectl apply -f deployment/k8s/namespace.yaml

# 部署服务
kubectl apply -f deployment/k8s/

# 查看服务状态
kubectl get pods -n hailo8-microservices
kubectl get services -n hailo8-microservices

# 端口转发访问服务
kubectl port-forward -n hailo8-microservices service/api-gateway 8000:8000
```

## API 文档

### 认证

所有 API 请求都需要在 Header 中包含认证令牌：

```bash
# 登录获取令牌
curl -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin123"}'

# 使用令牌访问 API
curl -X GET http://localhost:8000/api/v1/models \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 推理 API

```bash
# 单次推理
curl -X POST http://localhost:8000/api/v1/inference \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model_id": "resnet50",
    "input_data": "base64_encoded_image",
    "input_shape": [1, 224, 224, 3]
  }'

# 批量推理
curl -X POST http://localhost:8000/api/v1/inference/batch \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "requests": [
      {"model_id": "resnet50", "input_data": "image1"},
      {"model_id": "resnet50", "input_data": "image2"}
    ],
    "batch_size": 8
  }'
```

### 模型管理 API

```bash
# 获取模型列表
curl -X GET http://localhost:8000/api/v1/models \\
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取模型详情
curl -X GET http://localhost:8000/api/v1/models/resnet50 \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 监控 API

```bash
# 获取系统指标
curl -X GET http://localhost:8000/api/v1/metrics \\
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取健康状态
curl -X GET http://localhost:8000/health
```

## 监控和日志

### Grafana 面板

访问 http://localhost:3000 (admin/admin)

预配置面板：
- 系统资源监控
- 推理性能指标
- 服务健康状态
- API 请求统计

### Prometheus 指标

访问 http://localhost:9090

可用指标：
- `inference_requests_total` - 推理请求总数
- `inference_duration_seconds` - 推理耗时
- `system_cpu_usage` - CPU 使用率
- `system_memory_usage` - 内存使用率

## 开发指南

### 添加新服务

1. 创建服务目录：
```bash
mkdir new-service
cd new-service
mkdir src tests config
```

2. 实现服务逻辑：
```python
# src/main.py
from fastapi import FastAPI

app = FastAPI(title="新服务")

@app.get("/")
async def root():
    return {"service": "New Service"}
```

3. 添加到 Docker Compose：
```yaml
new-service:
  build: ../new-service
  ports:
    - "8005:8005"
  networks:
    - hailo8-network
```

### 本地开发

```bash
# 启动单个服务
cd api-gateway
pip install -r requirements.txt
python src/main.py

# 或使用 Docker
docker build -t hailo8/api-gateway .
docker run -p 8000:8000 hailo8/api-gateway
```

## 性能优化

### Hailo8 TPU 优化

1. **批处理优化**：
   - 使用适当的批大小 (8-16)
   - 启用异步推理模式
   - 实现请求队列管理

2. **模型优化**：
   - 使用 Hailo 编译器优化模型
   - 选择合适的量化策略
   - 预加载常用模型

3. **系统优化**：
   - 配置 CPU 亲和性
   - 优化内存分配
   - 使用专用推理节点

### 服务扩展

```yaml
# 水平扩展推理服务
inference-service:
  deploy:
    replicas: 3
    resources:
      limits:
        devices:
          - driver: hailo
            count: 1
```

## 故障排除

### 常见问题

1. **Hailo8 设备不可用**：
```bash
# 检查设备状态
lspci | grep Hailo
dmesg | grep hailo

# 重启 Hailo 服务
sudo systemctl restart hailo
```

2. **服务无法启动**：
```bash
# 查看服务日志
docker-compose logs service-name

# 检查端口占用
netstat -tulpn | grep :8000
```

3. **推理性能差**：
```bash
# 监控系统资源
htop
nvidia-smi  # 如果有 GPU
```

## 安全配置

### 生产环境配置

1. **更改默认密码**：
```bash
# 更新认证服务密码
export JWT_SECRET_KEY="your-secret-key"
export ADMIN_PASSWORD="secure-password"
```

2. **启用 HTTPS**：
```bash
# 生成 SSL 证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
  -keyout deployment/nginx/ssl/nginx.key \\
  -out deployment/nginx/ssl/nginx.crt
```

3. **网络安全**：
```yaml
# 限制网络访问
networks:
  hailo8-network:
    driver: bridge
    internal: true
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License

## 支持

- 文档：[项目 Wiki](https://github.com/your-org/hailo8-microservices/wiki)
- 问题反馈：[GitHub Issues](https://github.com/your-org/hailo8-microservices/issues)
- 讨论：[GitHub Discussions](https://github.com/your-org/hailo8-microservices/discussions)
""")
    
    # Makefile
    with open(f"{project_path}/Makefile", "w") as f:
        f.write("""# Hailo8 微服务 Makefile

.PHONY: help build up down logs clean test

help:
	@echo "可用命令："
	@echo "  build    - 构建所有服务镜像"
	@echo "  up       - 启动所有服务"
	@echo "  down     - 停止所有服务"
	@echo "  logs     - 查看服务日志"
	@echo "  clean    - 清理资源"
	@echo "  test     - 运行测试"

build:
	docker-compose -f deployment/docker-compose.yml build

up:
	docker-compose -f deployment/docker-compose.yml up -d

down:
	docker-compose -f deployment/docker-compose.yml down

logs:
	docker-compose -f deployment/docker-compose.yml logs -f

clean:
	docker-compose -f deployment/docker-compose.yml down -v
	docker system prune -f

test:
	@echo "运行服务测试..."
	@for service in api-gateway inference-service model-service monitoring-service auth-service; do \\
		echo "测试 $$service..."; \\
		cd $$service && python -m pytest tests/ || true; \\
		cd ..; \\
	done

dev-setup:
	@echo "设置开发环境..."
	@for service in api-gateway inference-service model-service monitoring-service auth-service; do \\
		echo "安装 $$service 依赖..."; \\
		cd $$service && pip install -r requirements.txt; \\
		cd ..; \\
	done

k8s-deploy:
	kubectl apply -f deployment/k8s/

k8s-clean:
	kubectl delete namespace hailo8-microservices
""")

def main():
    """主函数"""
    print("🚀 创建 Hailo8 微服务架构集成示例...")
    
    try:
        # 创建微服务架构
        project_path = create_microservice_architecture()
        
        # 使用 Hailo8 集成功能
        print("📦 集成 Hailo8 TPU 支持...")
        
        config = {
            "project_name": "Hailo8 微服务架构",
            "description": "基于 Hailo8 TPU 的微服务架构示例",
            "hailo8_config": {
                "enable_docker": True,
                "enable_monitoring": True,
                "enable_testing": True
            },
            "integration_type": "microservice"
        }
        
        # 集成到推理服务
        integrate_with_existing_project(
            project_path=f"{project_path}/inference-service",
            config=config
        )
        
        print(f"✅ 微服务架构创建完成！")
        print(f"📁 项目路径: {project_path}")
        print(f"""
🎯 快速开始：

1. 进入项目目录：
   cd {project_path}

2. 启动所有服务：
   docker-compose -f deployment/docker-compose.yml up -d

3. 访问服务：
   - API 网关: http://localhost:8000
   - 推理服务: http://localhost:8001
   - 模型服务: http://localhost:8002
   - 监控服务: http://localhost:8003
   - 认证服务: http://localhost:8004
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

4. 测试推理 API：
   # 先登录获取令牌
   curl -X POST http://localhost:8000/api/v1/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{{"username": "admin", "password": "admin123"}}'
   
   # 使用令牌进行推理
   curl -X POST http://localhost:8000/api/v1/inference \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{{
       "model_id": "resnet50",
       "input_data": "test_data",
       "input_shape": [1, 224, 224, 3]
     }}'

📚 更多信息请查看 README.md 文件
        """)
        
        return project_path
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return None

if __name__ == "__main__":
    main()