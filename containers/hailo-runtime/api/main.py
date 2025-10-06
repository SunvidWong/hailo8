#!/usr/bin/env python3
"""
Hailo8 Runtime API Service
主API服务入口，提供RESTful API和gRPC接口
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from api import inference, models, device
from api.config import settings
from api.frigate_adapter import frigate_router, init_frigate_adapter

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
hailo_inference_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化Hailo服务和Frigate适配器，关闭时清理资源
    """
    global hailo_inference_service

    logger.info("🚀 启动Hailo8 Runtime API服务...")

    try:
        # 初始化Hailo推理服务
        hailo_inference_service = inference.HailoInferenceService()
        await hailo_inference_service.initialize()

        # 初始化Frigate适配器
        await init_frigate_adapter()

        # 启动gRPC服务
        grpc_task = asyncio.create_task(
            inference.start_grpc_server(settings.GRPC_PORT)
        )

        logger.info("✅ Hailo8服务初始化完成")
        logger.info("✅ Frigate适配器初始化完成")

        yield

    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise
    finally:
        # 清理资源
        logger.info("🔄 清理服务资源...")
        if hailo_inference_service:
            await hailo_inference_service.cleanup()

        # 等待gRPC服务关闭
        if 'grpc_task' in locals():
            grpc_task.cancel()
            try:
                await grpc_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ 服务关闭完成")


# 创建FastAPI应用
app = FastAPI(
    title="Hailo8 Runtime API",
    description="Hailo8 AI推理服务API - 支持Frigate集成",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "service": "Hailo8 Runtime API",
        "version": "1.0.0",
        "frigate_support": True,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "api": "/api/v1",
            "frigate": "/frigate",
            "docs": "/docs"
        }
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """简单健康检查"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


# 就绪检查端点
@app.get("/ready")
async def readiness_check():
    """就绪状态检查，检查Hailo服务是否可用"""
    if not hailo_inference_service or not hailo_inference_service.is_ready():
        raise HTTPException(status_code=503, detail="Service not ready")

    return {
        "status": "ready",
        "device_status": await hailo_inference_service.get_device_status(),
        "frigate_adapter": await frigate_adapter.health_check()
    }


# 注册API路由
app.include_router(
    inference.router,
    prefix="/api/v1/inference",
    tags=["inference"]
)

app.include_router(
    models.router,
    prefix="/api/v1/models",
    tags=["models"]
)

app.include_router(
    device.router,
    prefix="/api/v1/device",
    tags=["device"]
)

# 注册Frigate API路由
app.include_router(
    frigate_router,
    tags=["frigate"]
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "服务器内部错误"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# 信号处理
def signal_handler(signum, frame):
    """处理关闭信号"""
    logger.info(f"接收到信号 {signum}，准备关闭服务...")
    sys.exit(0)


# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def main():
    """主函数"""
    logger.info(f"🚀 启动Hailo8 Runtime API服务")
    logger.info(f"📝 配置: {settings.dict()}")

    # 检查是否启用Frigate模式
    frigate_mode = os.getenv('FRIGATE_MODE', 'false').lower() == 'true'
    if frigate_mode:
        logger.info("🔗 Frigate集成模式已启用")

    # 启动uvicorn服务器
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )


if __name__ == "__main__":
    main()