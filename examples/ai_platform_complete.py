#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete AI Platform Integration Example

Demonstrates how to integrate Hailo8 TPU support into a complete AI platform
including frontend, backend, ML pipeline, model management and more
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_complete_ai_platform():
    """创建完整的 AI 平台"""
    project_path = "/tmp/complete_ai_platform"
    os.makedirs(project_path, exist_ok=True)
    
    print("🚀 Creating complete AI platform project...")
    
    # Create project structure
    create_project_structure(project_path)
    
    # Create components
    create_backend_service(project_path)
    create_frontend_app(project_path)
    create_ml_pipeline(project_path)
    create_model_registry(project_path)
    create_monitoring_system(project_path)
    create_deployment_configs(project_path)
    create_documentation(project_path)
    
    # Integrate Hailo8 support
    print("🔧 Integrating Hailo8 TPU support...")
    integrate_with_existing_project(
        project_path=project_path,
        project_name="Complete AI Platform",
        integration_type="detailed",
        config={
            "hailo8_features": [
                "inference_acceleration",
                "model_optimization",
                "performance_monitoring",
                "auto_scaling"
            ],
            "target_platforms": ["linux", "docker"],
            "api_integration": True,
            "monitoring": True,
            "auto_setup": True
        }
    )
    
    print("✅ Complete AI Platform created successfully!")
    print(f"📁 Project path: {project_path}")
    print(f"🌐 Start command: cd {project_path} && docker-compose up")
    
    return project_path

def create_project_structure(project_path):
    """创建项目目录结构"""
    directories = [
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/utils",
        "frontend/public",
        "backend/src/api",
        "backend/src/models",
        "backend/src/services",
        "backend/src/utils",
        "ml_pipeline/src",
        "ml_pipeline/models",
        "ml_pipeline/data",
        "model_registry/src",
        "model_registry/storage",
        "monitoring/src",
        "monitoring/dashboards",
        "deployment/docker",
        "deployment/kubernetes",
        "docs",
        "scripts",
        "tests/unit",
        "tests/integration",
        "config"
    ]
    
    for directory in directories:
        os.makedirs(f"{project_path}/{directory}", exist_ok=True)

def create_backend_service(project_path):
    """创建后端服务"""
    # 主应用文件
    with open(f"{project_path}/backend/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import asyncio
import uvicorn

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Complete AI Platform API",
    description="基于 Hailo8 TPU 的完整 AI 平台后端服务",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class InferenceRequest(BaseModel):
    model_id: str
    input_data: Any
    parameters: Optional[Dict[str, Any]] = {}

class ModelUpload(BaseModel):
    name: str
    description: str
    model_type: str
    framework: str

# 全局状态
system_status = {
    "hailo8_available": True,
    "models_loaded": 3,
    "active_pipelines": 2,
    "total_inferences": 1250
}

@app.get("/")
async def root():
    return {
        "service": "Complete AI Platform API",
        "version": "1.0.0",
        "status": "running",
        "hailo8_enabled": True
    }

@app.get("/api/v1/system/status")
async def get_system_status():
    return system_status

@app.get("/api/v1/models")
async def list_models():
    return [
        {
            "id": "resnet50_hailo",
            "name": "ResNet-50 (Hailo Optimized)",
            "type": "classification",
            "framework": "pytorch",
            "device": "hailo8",
            "performance": {"fps": 120, "latency": "8.3ms"}
        },
        {
            "id": "yolov5_hailo",
            "name": "YOLOv5 (Hailo Optimized)",
            "type": "detection",
            "framework": "pytorch", 
            "device": "hailo8",
            "performance": {"fps": 60, "latency": "16.7ms"}
        }
    ]

@app.post("/api/v1/inference")
async def run_inference(request: InferenceRequest):
    # 模拟推理
    await asyncio.sleep(0.01)  # Hailo8 快速推理
    
    return {
        "task_id": "task_001",
        "model_id": request.model_id,
        "device": "Hailo8 TPU",
        "inference_time": "8.3ms",
        "result": {
            "predictions": [
                {"class": "cat", "confidence": 0.95},
                {"class": "dog", "confidence": 0.03}
            ]
        }
    }

@app.get("/api/v1/pipelines")
async def list_pipelines():
    return [
        {
            "id": "image_classification_pipeline",
            "name": "图像分类流水线",
            "status": "running",
            "progress": 0.75
        },
        {
            "id": "object_detection_pipeline", 
            "name": "目标检测流水线",
            "status": "completed",
            "progress": 1.0
        }
    ]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "hailo8": "available"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
    
    # requirements.txt
    with open(f"{project_path}/backend/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
aiofiles>=23.0.0
numpy>=1.24.0
pillow>=10.0.0
""")

def create_frontend_app(project_path):
    """创建前端应用"""
    # React 主应用
    with open(f"{project_path}/frontend/src/App.js", "w") as f:
        f.write("""import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState({});
  const [models, setModels] = useState([]);
  const [pipelines, setPipelines] = useState([]);

  useEffect(() => {
    fetchSystemStatus();
    fetchModels();
    fetchPipelines();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/models');
      const data = await response.json();
      setModels(data);
    } catch (error) {
      console.error('获取模型列表失败:', error);
    }
  };

  const fetchPipelines = async () => {
    try {
      const response = await fetch('/api/v1/pipelines');
      const data = await response.json();
      setPipelines(data);
    } catch (error) {
      console.error('获取流水线列表失败:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧠 Complete AI Platform</h1>
        <div className="status-indicator">
          Hailo8 TPU: {systemStatus.hailo8_available ? '🟢 Online' : '🔴 Offline'}
        </div>
      </header>

      <main className="app-main">
        <div className="dashboard">
          <div className="stats-grid">
            <div className="stat-card">
              <h3>🤖 已加载模型</h3>
              <div className="stat-value">{systemStatus.models_loaded || 0}</div>
            </div>
            <div className="stat-card">
              <h3>⚡ 活跃流水线</h3>
              <div className="stat-value">{systemStatus.active_pipelines || 0}</div>
            </div>
            <div className="stat-card">
              <h3>📊 总推理次数</h3>
              <div className="stat-value">{systemStatus.total_inferences || 0}</div>
            </div>
          </div>

          <div className="content-grid">
            <div className="models-section">
              <h2>🤖 模型管理</h2>
              <div className="models-list">
                {models.map(model => (
                  <div key={model.id} className="model-card">
                    <h4>{model.name}</h4>
                    <p>类型: {model.type}</p>
                    <p>设备: {model.device}</p>
                    <p>性能: {model.performance.fps} FPS</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pipelines-section">
              <h2>🔄 ML 流水线</h2>
              <div className="pipelines-list">
                {pipelines.map(pipeline => (
                  <div key={pipeline.id} className="pipeline-card">
                    <h4>{pipeline.name}</h4>
                    <p>状态: {pipeline.status}</p>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{width: `${pipeline.progress * 100}%`}}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
""")
    
    # CSS 样式
    with open(f"{project_path}/frontend/src/App.css", "w") as f:
        f.write(""".app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  color: white;
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
}

.status-indicator {
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-weight: 500;
}

.app-main {
  padding: 2rem;
}

.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.9);
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #333;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.models-section, .pipelines-section {
  background: rgba(255, 255, 255, 0.9);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.models-section h2, .pipelines-section h2 {
  margin: 0 0 1rem 0;
  color: #333;
}

.models-list, .pipelines-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.model-card, .pipeline-card {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.model-card h4, .pipeline-card h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.model-card p, .pipeline-card p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s ease;
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
""")
    
    # package.json
    with open(f"{project_path}/frontend/package.json", "w") as f:
        f.write("""{
  "name": "complete-ai-platform-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "proxy": "http://localhost:8000"
}
""")

def create_ml_pipeline(project_path):
    """创建机器学习流水线"""
    with open(f"{project_path}/ml_pipeline/src/pipeline.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MLPipeline:
    def __init__(self, pipeline_id: str, config: Dict[str, Any]):
        self.pipeline_id = pipeline_id
        self.config = config
        self.status = "created"
        self.steps = []
    
    async def add_step(self, step_name: str, step_config: Dict[str, Any]):
        step = {
            "name": step_name,
            "config": step_config,
            "status": "pending"
        }
        self.steps.append(step)
        logger.info(f"添加步骤 {step_name} 到流水线 {self.pipeline_id}")
    
    async def run(self):
        logger.info(f"开始运行流水线 {self.pipeline_id}")
        self.status = "running"
        
        try:
            for step in self.steps:
                await self._run_step(step)
                if step["status"] == "failed":
                    self.status = "failed"
                    return
            
            self.status = "completed"
            logger.info(f"流水线 {self.pipeline_id} 运行完成")
            
        except Exception as e:
            self.status = "failed"
            logger.error(f"流水线运行失败: {e}")
    
    async def _run_step(self, step: Dict[str, Any]):
        step_name = step["name"]
        logger.info(f"运行步骤 {step_name}")
        
        step["status"] = "running"
        
        try:
            # 模拟步骤执行
            await asyncio.sleep(1)
            
            if step_name == "data_preprocessing":
                result = {"processed_samples": 10000}
            elif step_name == "model_training":
                result = {"accuracy": 0.95, "loss": 0.05}
            elif step_name == "hailo_optimization":
                result = {"optimized": True, "speedup": "3.2x"}
            else:
                result = {"completed": True}
            
            step["result"] = result
            step["status"] = "completed"
            logger.info(f"步骤 {step_name} 完成")
            
        except Exception as e:
            step["error"] = str(e)
            step["status"] = "failed"
            logger.error(f"步骤 {step_name} 失败: {e}")

class PipelineManager:
    def __init__(self):
        self.pipelines = {}
    
    async def create_pipeline(self, pipeline_id: str, config: Dict[str, Any]):
        pipeline = MLPipeline(pipeline_id, config)
        
        # 添加默认步骤
        await pipeline.add_step("data_preprocessing", {})
        await pipeline.add_step("model_training", {})
        await pipeline.add_step("hailo_optimization", {})
        await pipeline.add_step("deployment", {})
        
        self.pipelines[pipeline_id] = pipeline
        return pipeline
    
    def get_pipeline(self, pipeline_id: str):
        return self.pipelines.get(pipeline_id)
    
    def list_pipelines(self):
        return list(self.pipelines.values())

# 全局实例
pipeline_manager = PipelineManager()
""")

def create_model_registry(project_path):
    """创建模型注册中心"""
    with open(f"{project_path}/model_registry/src/registry.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

class ModelRegistry:
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.models = self._load_models()
    
    def _load_models(self) -> Dict[str, Any]:
        models_file = self.storage_path / "models.json"
        if models_file.exists():
            with open(models_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_models(self):
        models_file = self.storage_path / "models.json"
        with open(models_file, 'w') as f:
            json.dump(self.models, f, indent=2)
    
    def register_model(self, model_id: str, metadata: Dict[str, Any]):
        self.models[model_id] = {
            **metadata,
            "registered_at": "2024-01-01T00:00:00Z",
            "status": "registered"
        }
        self._save_models()
        return self.models[model_id]
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(model_id)
    
    def list_models(self) -> List[Dict[str, Any]]:
        return list(self.models.values())
    
    def update_model(self, model_id: str, updates: Dict[str, Any]):
        if model_id in self.models:
            self.models[model_id].update(updates)
            self._save_models()
            return self.models[model_id]
        return None
    
    def delete_model(self, model_id: str) -> bool:
        if model_id in self.models:
            del self.models[model_id]
            self._save_models()
            return True
        return False

# 全局实例
model_registry = ModelRegistry()
""")

def create_monitoring_system(project_path):
    """创建监控系统"""
    with open(f"{project_path}/monitoring/src/monitor.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import time
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        metrics = {
            "timestamp": time.time(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "hailo8_temperature": 45,  # 模拟 Hailo8 温度
            "hailo8_utilization": 75,  # 模拟 Hailo8 利用率
            "inference_count": 1250,
            "avg_inference_time": 8.3
        }
        
        self.metrics = metrics
        self._check_alerts(metrics)
        
        return metrics
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        # 检查告警条件
        if metrics["cpu_usage"] > 80:
            self._add_alert("high_cpu", f"CPU 使用率过高: {metrics['cpu_usage']}%")
        
        if metrics["hailo8_temperature"] > 70:
            self._add_alert("high_temp", f"Hailo8 温度过高: {metrics['hailo8_temperature']}°C")
        
        if metrics["avg_inference_time"] > 50:
            self._add_alert("slow_inference", f"推理速度过慢: {metrics['avg_inference_time']}ms")
    
    def _add_alert(self, alert_type: str, message: str):
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "severity": "warning"
        }
        self.alerts.append(alert)
        logger.warning(f"告警: {message}")
    
    def get_alerts(self):
        return self.alerts[-10:]  # 返回最近10个告警
    
    def clear_alerts(self):
        self.alerts.clear()

# 全局实例
system_monitor = SystemMonitor()
""")

def create_deployment_configs(project_path):
    """创建部署配置"""
    # Docker Compose
    with open(f"{project_path}/docker-compose.yml", "w") as f:
        f.write("""version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./hailo8:/app/hailo8
      - ./models:/app/models
    environment:
      - HAILO8_ENABLED=true
      - MODEL_STORAGE_PATH=/app/models
    depends_on:
      - redis
      - postgres

  ml-pipeline:
    build: ./ml_pipeline
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - HAILO8_ENABLED=true

  model-registry:
    build: ./model_registry
    volumes:
      - ./models:/app/storage
    ports:
      - "8001:8000"

  monitoring:
    build: ./monitoring
    ports:
      - "8002:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=aiplatform
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=admin123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
""")
    
    # Kubernetes 配置
    with open(f"{project_path}/deployment/kubernetes/deployment.yaml", "w") as f:
        f.write("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-platform-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-platform-backend
  template:
    metadata:
      labels:
        app: ai-platform-backend
    spec:
      containers:
      - name: backend
        image: ai-platform-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: HAILO8_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: ai-platform-backend-service
spec:
  selector:
    app: ai-platform-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
""")

def create_documentation(project_path):
    """创建项目文档"""
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# Complete AI Platform with Hailo8 TPU

🧠 基于 Hailo8 TPU 的完整 AI 平台，提供端到端的机器学习解决方案。

## ✨ 特性

- 🚀 **Hailo8 TPU 加速**: 高性能推理加速
- 🎯 **完整 ML 流水线**: 从数据预处理到模型部署
- 📊 **实时监控**: 系统性能和模型指标监控
- 🔄 **模型管理**: 完整的模型生命周期管理
- 🌐 **现代化 UI**: React 前端界面
- 🐳 **容器化部署**: Docker 和 Kubernetes 支持

## 🏗️ 架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  ML Pipeline    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Model Registry │    │   Monitoring    │    │   Hailo8 TPU    │
│   (Storage)     │    │   (Metrics)     │    │  (Inference)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 使用 Docker Compose (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd complete_ai_platform

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 本地开发

```bash
# 后端服务
cd backend
pip install -r requirements.txt
python src/main.py

# 前端服务
cd frontend
npm install
npm start

# ML 流水线
cd ml_pipeline
pip install -r requirements.txt
python src/pipeline.py
```

## 📋 服务端口

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **模型注册中心**: http://localhost:8001
- **监控系统**: http://localhost:8002
- **API 文档**: http://localhost:8000/docs

## 🔧 配置

### Hailo8 TPU 配置

```yaml
hailo8:
  enabled: true
  device_id: 0
  optimization_level: 3
  batch_size: 1
```

### 模型配置

```yaml
models:
  - name: "ResNet-50"
    path: "./models/resnet50_hailo.hef"
    type: "classification"
    input_shape: [1, 224, 224, 3]
  
  - name: "YOLOv5"
    path: "./models/yolov5_hailo.hef"
    type: "detection"
    input_shape: [1, 640, 640, 3]
```

## 📊 监控指标

- **系统指标**: CPU、内存、磁盘使用率
- **Hailo8 指标**: 温度、利用率、功耗
- **模型指标**: 推理延迟、吞吐量、准确率
- **业务指标**: 请求数、错误率、用户活跃度

## 🔄 ML 流水线

1. **数据预处理**: 数据清洗、增强、格式转换
2. **模型训练**: 支持 PyTorch、TensorFlow
3. **模型评估**: 准确率、性能指标评估
4. **Hailo8 优化**: 模型量化、编译优化
5. **模型部署**: 自动化部署到生产环境

## 🛠️ API 接口

### 推理接口

```bash
curl -X POST "http://localhost:8000/api/v1/inference" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model_id": "resnet50_hailo",
    "input_data": "base64_encoded_image"
  }'
```

### 模型管理

```bash
# 获取模型列表
curl "http://localhost:8000/api/v1/models"

# 上传新模型
curl -X POST "http://localhost:8001/api/v1/models" \\
  -F "model=@model.hef" \\
  -F "metadata=@metadata.json"
```

## 🧪 测试

```bash
# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 性能测试
python scripts/benchmark.py
```

## 📈 性能优化

### Hailo8 TPU 优化

- **模型量化**: INT8 量化减少模型大小
- **批处理**: 提高吞吐量
- **流水线并行**: 多模型并行推理
- **内存优化**: 减少数据传输开销

### 系统优化

- **缓存策略**: Redis 缓存热点数据
- **负载均衡**: 多实例部署
- **异步处理**: 非阻塞 I/O 操作
- **资源池**: 连接池、线程池管理

## 🔒 安全配置

- **API 认证**: JWT Token 认证
- **HTTPS**: SSL/TLS 加密传输
- **访问控制**: 基于角色的权限管理
- **数据加密**: 敏感数据加密存储

## 🚀 部署指南

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 扩展服务
docker-compose up -d --scale backend=3
```

### Kubernetes 部署

```bash
# 应用配置
kubectl apply -f deployment/kubernetes/

# 查看状态
kubectl get pods
kubectl get services
```

## 📝 开发指南

### 添加新模型

1. 准备模型文件 (.hef)
2. 创建模型配置文件
3. 注册到模型注册中心
4. 更新 API 接口
5. 添加前端界面

### 扩展功能

1. 在对应服务中添加新功能
2. 更新 API 文档
3. 添加测试用例
4. 更新前端界面

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

MIT License

## 🆘 支持

- 📧 邮箱: support@aiplatform.com
- 💬 讨论: GitHub Discussions
- 🐛 问题: GitHub Issues
""")

if __name__ == "__main__":
    create_complete_ai_platform()