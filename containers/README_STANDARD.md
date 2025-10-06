# 标准Docker Compose配置

这是一个标准的Docker Compose配置文件，用于部署Hailo8 + NVIDIA AI加速服务。

## 🚀 快速启动

```bash
# 启动AI加速服务
docker-compose -f docker-compose.standard.yml up -d

# 查看服务状态
docker-compose -f docker-compose.standard.yml ps

# 查看日志
docker-compose -f docker-compose.standard.yml logs -f
```

## 📱 访问地址

- **AI加速API**: http://localhost:8000
- **Redis**: localhost:6379

## 🔧 API端点

```bash
# 检查硬件状态
curl http://localhost:8000/ai/hardware

# 自动推理测试
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"image":[[[255,0,0]]],"engine":"auto"}' \
  http://localhost:8000/ai/infer

# 健康检查
curl http://localhost:8000/health
```

## 📂 目录结构

```
.
├── docker-compose.standard.yml
├── models/                  # AI模型文件
├── logs/                    # 日志文件
└── hailo-runtime/           # AI服务源码
```

## ⚙️ 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SUPPORT_HAILO` | `true` | 启用Hailo8支持 |
| `SUPPORT_NVIDIA` | `true` | 启用NVIDIA支持 |
| `DEFAULT_ENGINE` | `auto` | 默认推理引擎 |

## 🔍 硬件要求

- **Hailo8**: PCIe AI加速卡 (可选)
- **NVIDIA**: GPU with CUDA support (可选)
- **系统**: Linux with Docker support