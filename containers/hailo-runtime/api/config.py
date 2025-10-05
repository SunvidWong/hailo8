"""
配置管理模块
使用Pydantic进行配置验证和管理
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置类"""

    # API服务配置
    API_HOST: str = Field(default="0.0.0.0", description="API服务主机地址")
    API_PORT: int = Field(default=8000, description="API服务端口")
    GRPC_PORT: int = Field(default=50051, description="gRPC服务端口")

    # 调试配置
    DEBUG: bool = Field(default=False, description="调试模式")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")

    # 跨域配置
    CORS_ORIGINS: List[str] = Field(
        default=["*"], description="允许的CORS源"
    )

    # Hailo配置
    HAILO_MODEL_PATH: str = Field(
        default="/app/models", description="模型文件路径"
    )
    HAILO_DEVICE_ID: Optional[str] = Field(
        default=None, description="指定Hailo设备ID"
    )
    HAILO_BATCH_SIZE: int = Field(default=1, description="推理批次大小")

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存过期时间(秒)")
    MAX_CACHE_SIZE: int = Field(default=1000, description="最大缓存条目数")

    # 安全配置
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_EXPIRATION: int = Field(default=86400, description="JWT过期时间(秒)")

    # 限制配置
    MAX_REQUEST_SIZE: int = Field(default=50 * 1024 * 1024, description="最大请求大小(字节)")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, description="最大并发请求数")

    # 监控配置
    METRICS_ENABLED: bool = Field(default=True, description="是否启用指标收集")
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus指标端口")

    # 性能配置
    WORKER_THREADS: int = Field(default=4, description="工作线程数")
    INFERENCE_TIMEOUT: int = Field(default=30, description="推理超时时间(秒)")

    # 日志配置
    LOG_FILE: Optional[str] = Field(
        default="/app/logs/api.log", description="日志文件路径"
    )
    LOG_ROTATION: str = Field(
        default="1 day", description="日志轮转周期"
    )
    LOG_RETENTION: str = Field(
        default="7 days", description="日志保留时间"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def api_url(self) -> str:
        """获取API URL"""
        return f"http://{self.API_HOST}:{self.API_PORT}"

    @property
    def grpc_url(self) -> str:
        """获取gRPC URL"""
        return f"{self.API_HOST}:{self.GRPC_PORT}"

    def get_model_path(self, model_name: str) -> str:
        """获取模型完整路径"""
        return str(self.HAILO_MODEL_PATH / model_name)


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()