#!/usr/bin/env python3
"""
Hailo8 Docker 硬件加速服务
提供HTTP API接口供其他容器调用Hailo8硬件加速功能
"""

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入自定义模块
from hailo8_manager import Hailo8Manager
from models import *
from config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局Hailo8管理器实例
hailo8_manager: Optional[Hailo8Manager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global hailo8_manager
    
    # 启动时初始化
    logger.info("正在启动Hailo8服务...")
    try:
        hailo8_manager = Hailo8Manager()
        await hailo8_manager.initialize()
        logger.info("Hailo8服务启动成功")
    except Exception as e:
        logger.error(f"Hailo8服务启动失败: {e}")
        # 即使硬件不可用，也继续启动服务（用于测试）
        hailo8_manager = Hailo8Manager(mock_mode=True)
        await hailo8_manager.initialize()
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭Hailo8服务...")
    if hailo8_manager:
        await hailo8_manager.cleanup()
    logger.info("Hailo8服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="Hailo8 硬件加速服务",
    description="提供Hailo8 AI推理硬件加速的Docker容器服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 健康检查和状态接口 ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        if hailo8_manager:
            status = await hailo8_manager.get_health_status()
            return HealthResponse(
                status="healthy" if status["healthy"] else "unhealthy",
                timestamp=status["timestamp"],
                details=status
            )
        else:
            return HealthResponse(
                status="unhealthy",
                details={"error": "Hailo8管理器未初始化"}
            )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            details={"error": str(e)}
        )

@app.get("/devices", response_model=List[DeviceInfo])
async def get_devices():
    """获取Hailo8设备信息"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        devices = await hailo8_manager.get_devices()
        return devices
    except Exception as e:
        logger.error(f"获取设备信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=ServiceStatus)
async def get_service_status():
    """获取服务状态"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        status = await hailo8_manager.get_service_status()
        return ServiceStatus(**status)
    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 模型管理接口 ====================

@app.post("/models/load", response_model=ModelLoadResponse)
async def load_model(request: ModelLoadRequest):
    """加载模型"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        result = await hailo8_manager.load_model(
            model_path=request.model_path,
            model_id=request.model_id,
            device_id=request.device_id
        )
        
        return ModelLoadResponse(
            success=result["success"],
            model_id=result["model_id"],
            message=result.get("message", ""),
            details=result.get("details", {})
        )
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/models/{model_id}")
async def unload_model(model_id: str):
    """卸载模型"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        result = await hailo8_manager.unload_model(model_id)
        
        if result["success"]:
            return {"message": f"模型 {model_id} 卸载成功"}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "卸载失败"))
    except Exception as e:
        logger.error(f"卸载模型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """获取已加载模型列表"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        models = await hailo8_manager.list_models()
        return models
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 推理服务接口 ====================

@app.post("/inference", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """执行推理"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        result = await hailo8_manager.run_inference(
            model_id=request.model_id,
            input_data=request.input_data,
            input_format=request.input_format,
            output_format=request.output_format
        )
        
        return InferenceResponse(
            success=result["success"],
            task_id=result.get("task_id"),
            output_data=result.get("output_data"),
            inference_time=result.get("inference_time"),
            message=result.get("message", ""),
            details=result.get("details", {})
        )
    except Exception as e:
        logger.error(f"推理执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inference/batch", response_model=BatchInferenceResponse)
async def run_batch_inference(request: BatchInferenceRequest):
    """批量推理"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        result = await hailo8_manager.run_batch_inference(
            model_id=request.model_id,
            input_batch=request.input_batch,
            input_format=request.input_format,
            output_format=request.output_format,
            batch_size=request.batch_size
        )
        
        return BatchInferenceResponse(
            success=result["success"],
            task_id=result.get("task_id"),
            batch_results=result.get("batch_results", []),
            total_time=result.get("total_time"),
            message=result.get("message", ""),
            details=result.get("details", {})
        )
    except Exception as e:
        logger.error(f"批量推理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inference/{task_id}", response_model=TaskStatusResponse)
async def get_inference_result(task_id: str):
    """获取异步推理结果"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        result = await hailo8_manager.get_task_result(task_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskStatusResponse(**result)
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 监控和统计接口 ====================

@app.get("/metrics")
async def get_metrics():
    """获取Prometheus格式的监控指标"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        metrics = await hailo8_manager.get_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"获取监控指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=ServiceStats)
async def get_service_stats():
    """获取服务统计信息"""
    try:
        if not hailo8_manager:
            raise HTTPException(status_code=503, detail="Hailo8管理器未初始化")
        
        stats = await hailo8_manager.get_service_stats()
        return ServiceStats(**stats)
    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 错误处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": asyncio.get_event_loop().time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "details": str(exc) if settings.DEBUG else "请联系管理员",
            "status_code": 500,
            "timestamp": asyncio.get_event_loop().time()
        }
    )

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    workers = int(os.getenv("WORKERS", "1"))
    
    logger.info(f"启动Hailo8服务: {host}:{port}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        reload=settings.DEBUG
    )