"""
Hailo8服务配置管理
支持环境变量和配置文件
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """服务配置类"""
    
    # ==================== 基础服务配置 ====================
    
    # 服务基本信息
    SERVICE_NAME: str = Field("hailo8-service", description="服务名称")
    SERVICE_VERSION: str = Field("1.0.0", description="服务版本")
    DEBUG: bool = Field(False, description="调试模式")
    
    # 网络配置
    HOST: str = Field("0.0.0.0", description="服务监听地址")
    PORT: int = Field(8080, description="服务端口")
    WORKERS: int = Field(1, description="工作进程数")
    
    # 日志配置
    LOG_LEVEL: str = Field("INFO", description="日志级别")
    LOG_FILE: Optional[str] = Field(None, description="日志文件路径")
    LOG_MAX_SIZE: int = Field(100, description="日志文件最大大小(MB)")
    LOG_BACKUP_COUNT: int = Field(5, description="日志文件备份数量")
    
    # ==================== Hailo8硬件配置 ====================
    
    # 设备配置
    HAILO_DEVICE_COUNT: int = Field(1, description="Hailo8设备数量")
    HAILO_DEVICE_IDS: List[str] = Field(default_factory=list, description="指定设备ID列表")
    HAILO_MOCK_MODE: bool = Field(False, description="模拟模式（无硬件时使用）")
    
    # 驱动配置
    HAILO_DRIVER_PATH: str = Field("/dev/hailo0", description="Hailo8设备路径")
    HAILO_FIRMWARE_PATH: Optional[str] = Field(None, description="固件路径")
    
    # 性能配置
    HAILO_MAX_BATCH_SIZE: int = Field(8, description="最大批处理大小")
    HAILO_INFERENCE_TIMEOUT: float = Field(30.0, description="推理超时时间(秒)")
    HAILO_DEVICE_TIMEOUT: float = Field(5.0, description="设备操作超时时间(秒)")
    
    # ==================== 模型管理配置 ====================
    
    # 模型路径
    MODEL_BASE_PATH: str = Field("/app/models", description="模型基础路径")
    MODEL_CACHE_SIZE: int = Field(5, description="模型缓存大小")
    MODEL_PRELOAD: List[str] = Field(default_factory=list, description="预加载模型列表")
    
    # 模型配置
    SUPPORTED_MODEL_FORMATS: List[str] = Field(
        default_factory=lambda: [".hef", ".onnx"],
        description="支持的模型格式"
    )
    MAX_MODEL_SIZE: int = Field(500, description="最大模型大小(MB)")
    
    # ==================== API服务配置 ====================
    
    # 并发控制
    MAX_CONCURRENT_REQUESTS: int = Field(10, description="最大并发请求数")
    MAX_CONCURRENT_INFERENCES: int = Field(5, description="最大并发推理数")
    REQUEST_TIMEOUT: float = Field(60.0, description="请求超时时间(秒)")
    
    # 数据处理
    MAX_INPUT_SIZE: int = Field(50, description="最大输入数据大小(MB)")
    MAX_BATCH_SIZE: int = Field(16, description="最大批处理大小")
    ENABLE_ASYNC_INFERENCE: bool = Field(True, description="启用异步推理")
    
    # 缓存配置
    ENABLE_RESULT_CACHE: bool = Field(True, description="启用结果缓存")
    CACHE_TTL: int = Field(3600, description="缓存过期时间(秒)")
    CACHE_MAX_SIZE: int = Field(1000, description="缓存最大条目数")
    
    # ==================== 监控和统计配置 ====================
    
    # 监控配置
    ENABLE_METRICS: bool = Field(True, description="启用监控指标")
    METRICS_PORT: int = Field(9090, description="监控指标端口")
    HEALTH_CHECK_INTERVAL: int = Field(30, description="健康检查间隔(秒)")
    
    # 统计配置
    ENABLE_STATS: bool = Field(True, description="启用统计功能")
    STATS_RETENTION_DAYS: int = Field(7, description="统计数据保留天数")
    
    # 性能监控
    MONITOR_DEVICE_TEMP: bool = Field(True, description="监控设备温度")
    MONITOR_MEMORY_USAGE: bool = Field(True, description="监控内存使用")
    MONITOR_CPU_USAGE: bool = Field(True, description="监控CPU使用")
    
    # ==================== 安全配置 ====================
    
    # API安全
    ENABLE_API_KEY: bool = Field(False, description="启用API密钥验证")
    API_KEY: Optional[str] = Field(None, description="API密钥")
    ENABLE_RATE_LIMIT: bool = Field(True, description="启用速率限制")
    RATE_LIMIT_PER_MINUTE: int = Field(100, description="每分钟请求限制")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"], description="CORS允许的源")
    CORS_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE"],
        description="CORS允许的方法"
    )
    
    # ==================== 存储配置 ====================
    
    # 临时文件
    TEMP_DIR: str = Field("/app/temp", description="临时文件目录")
    TEMP_FILE_TTL: int = Field(3600, description="临时文件过期时间(秒)")
    MAX_TEMP_SIZE: int = Field(1000, description="临时文件最大大小(MB)")
    
    # 日志存储
    LOG_DIR: str = Field("/app/logs", description="日志目录")
    ENABLE_LOG_ROTATION: bool = Field(True, description="启用日志轮转")
    
    # ==================== 开发和测试配置 ====================
    
    # 开发配置
    RELOAD_ON_CHANGE: bool = Field(False, description="代码变更时重载")
    ENABLE_SWAGGER: bool = Field(True, description="启用Swagger文档")
    ENABLE_REDOC: bool = Field(True, description="启用ReDoc文档")
    
    # 测试配置
    TEST_MODE: bool = Field(False, description="测试模式")
    MOCK_INFERENCE_DELAY: float = Field(0.1, description="模拟推理延迟(秒)")
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # 环境变量前缀
        env_prefix = "HAILO8_"
        
        # 字段别名
        fields = {
            "HOST": {"env": ["HAILO8_HOST", "HOST"]},
            "PORT": {"env": ["HAILO8_PORT", "PORT"]},
            "DEBUG": {"env": ["HAILO8_DEBUG", "DEBUG"]},
            "LOG_LEVEL": {"env": ["HAILO8_LOG_LEVEL", "LOG_LEVEL"]},
        }


# ==================== 配置实例 ====================

# 创建全局配置实例
settings = Settings()


# ==================== 配置验证函数 ====================

def validate_config() -> bool:
    """验证配置的有效性"""
    try:
        # 验证端口范围
        if not (1 <= settings.PORT <= 65535):
            raise ValueError(f"端口号无效: {settings.PORT}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if settings.LOG_LEVEL.upper() not in valid_log_levels:
            raise ValueError(f"日志级别无效: {settings.LOG_LEVEL}")
        
        # 验证工作进程数
        if settings.WORKERS < 1:
            raise ValueError(f"工作进程数无效: {settings.WORKERS}")
        
        # 验证超时时间
        if settings.HAILO_INFERENCE_TIMEOUT <= 0:
            raise ValueError(f"推理超时时间无效: {settings.HAILO_INFERENCE_TIMEOUT}")
        
        # 验证批处理大小
        if settings.HAILO_MAX_BATCH_SIZE < 1:
            raise ValueError(f"最大批处理大小无效: {settings.HAILO_MAX_BATCH_SIZE}")
        
        return True
        
    except Exception as e:
        print(f"配置验证失败: {e}")
        return False


def get_device_config() -> dict:
    """获取设备相关配置"""
    return {
        "device_count": settings.HAILO_DEVICE_COUNT,
        "device_ids": settings.HAILO_DEVICE_IDS,
        "device_path": settings.HAILO_DRIVER_PATH,
        "mock_mode": settings.HAILO_MOCK_MODE,
        "timeout": settings.HAILO_DEVICE_TIMEOUT,
        "max_batch_size": settings.HAILO_MAX_BATCH_SIZE,
    }


def get_api_config() -> dict:
    """获取API相关配置"""
    return {
        "host": settings.HOST,
        "port": settings.PORT,
        "workers": settings.WORKERS,
        "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
        "request_timeout": settings.REQUEST_TIMEOUT,
        "enable_swagger": settings.ENABLE_SWAGGER,
        "cors_origins": settings.CORS_ORIGINS,
    }


def get_model_config() -> dict:
    """获取模型相关配置"""
    return {
        "base_path": settings.MODEL_BASE_PATH,
        "cache_size": settings.MODEL_CACHE_SIZE,
        "preload": settings.MODEL_PRELOAD,
        "supported_formats": settings.SUPPORTED_MODEL_FORMATS,
        "max_size": settings.MAX_MODEL_SIZE,
    }


# ==================== 配置初始化 ====================

def init_config():
    """初始化配置"""
    # 验证配置
    if not validate_config():
        raise RuntimeError("配置验证失败")
    
    # 创建必要的目录
    os.makedirs(settings.MODEL_BASE_PATH, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    print(f"Hailo8服务配置初始化完成:")
    print(f"  - 服务地址: {settings.HOST}:{settings.PORT}")
    print(f"  - 调试模式: {settings.DEBUG}")
    print(f"  - 日志级别: {settings.LOG_LEVEL}")
    print(f"  - 模拟模式: {settings.HAILO_MOCK_MODE}")


# 自动初始化配置
if __name__ != "__main__":
    init_config()