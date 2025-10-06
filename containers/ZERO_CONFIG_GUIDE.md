# 🚀 零配置AI监控系统部署指南

## 🎯 概述

这是一个真正意义上的**零配置**解决方案，让您能够一键部署完整的AI监控系统，Frigate将自动发现并使用Hailo8和NVIDIA硬件进行AI推理加速。

**无需手动配置** - 脚本会自动：
- 🔍 检测可用硬件（Hailo8 + NVIDIA）
- 📝 生成Frigate配置文件
- 🚀 启动所有必要的服务
- 🔗 建立服务间的网络连接
- 📊 配置监控和可视化

## ⚡ 一键部署

### 方法1: 使用部署脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 一键部署
./deploy_zero_config.sh
```

### 方法2: 手动Docker Compose

```bash
# 启动所有服务
docker-compose -f docker-compose.zero-config.yml up -d

# 查看服务状态
docker-compose -f docker-compose.zero-config.yml ps
```

## 🔍 自动配置流程

部署脚本会按以下顺序自动配置：

### 1. 硬件检测阶段
```
[INFO] 检测可用硬件...
[SUCCESS] ✓ 检测到Hailo8 PCIe设备
[SUCCESS] ✓ 检测到NVIDIA GPU: NVIDIA GeForce RTX 4090 (24576MB)
```

### 2. 目录创建阶段
```
[STEP] 创建必要的目录...
[INFO]   创建目录: config
[INFO]   创建目录: logs
[INFO]   创建目录: models
[INFO]   创建目录: media/frigate
[SUCCESS] ✓ 目录结构创建完成
```

### 3. 服务启动阶段
```
[SERVICE] 启动AI加速服务...
[SUCCESS] ✓ AI加速服务已启动
[SERVICE] 启动MQTT和自动配置服务...
[SERVICE] 启动Frigate NVR...
[SERVICE] 启动监控服务...
```

### 4. 配置验证阶段
```
[STEP] 验证部署状态...
[SUCCESS] ✓ ai-acceleration-service 服务运行正常 (端口 8000)
[SUCCESS] ✓ frigate 服务运行正常 (端口 5000)
[SUCCESS] ✓ prometheus 服务运行正常 (端口 9090)
[SUCCESS] ✓ grafana 服务运行正常 (端口 3000)
[SUCCESS] ✓ Frigate配置文件已生成
```

## 🎛️ 访问地址

部署完成后，您可以通过以下地址访问各个服务：

| 服务 | 地址 | 用途 | 默认凭据 |
|------|------|------|----------|
| **Frigate Web界面** | http://localhost:5000 | 配置摄像头、查看监控画面 | 无需登录 |
| **Grafana监控** | http://localhost:3000 | AI性能监控面板 | admin / hailo8_frigate |
| **Prometheus** | http://localhost:9090 | 指标数据收集 | 无需登录 |
| **AI加速API** | http://localhost:8000 | AI推理服务接口 | 无需登录 |

## 📱 Frigate配置

### 自动生成的配置示例

系统会根据检测到的硬件自动生成Frigate配置：

```yaml
# 当检测到Hailo8和NVIDIA时
detectors:
  hailo8:
    type: remote
    api:
      url: http://ai-acceleration-service:8000/frigate/infer/hailo
      timeout: 10
      max_retries: 3
    model:
      width: 640
      height: 640

  nvidia:
    type: remote
    api:
      url: http://ai-acceleration-service:8000/frigate/infer/nvidia
      timeout: 15
      max_retries: 3
    model:
      width: 640
      height: 640

  auto:
    type: remote
    api:
      url: http://ai-acceleration-service:8000/frigate/infer/auto
      timeout: 20
      max_retries: 3
    model:
      width: 640
      height: 640
```

### Frigate摄像头配置

访问 http://localhost:5000 后，在配置文件中添加摄像头：

```yaml
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://your-camera-ip/stream
          roles:
            - detect
            - record
    detect:
      width: 640
      height: 480
      fps: 5
    objects:
      track:
        - person
        - car
        - bicycle
    zones:
      front_porch:
        coordinates: 100,100 500,100 500,400 100,400
```

## 🔧 API端点

### 硬件状态查询
```bash
curl http://localhost:8000/ai/hardware
```

### Frigate集成状态
```bash
curl http://localhost:8000/frigate/status
```

### AI推理测试
```bash
# 自动选择引擎
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "auto"
  }' \
  http://localhost:8000/ai/infer

# 强制使用Hailo8
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input_image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "hailo"
  }' \
  http://localhost:8000/frigate/infer/hailo
```

## 📊 监控面板

### Grafana仪表盘

访问 http://localhost:3000，使用以下凭据登录：
- **用户名**: admin
- **密码**: hailo8_frigate

仪表盘包含：
- 🎯 AI推理性能指标
- 💾 硬件使用情况
- 📈 检测统计
- ⚡ 实时性能监控

### 关键指标

| 指标 | 描述 | 正常范围 |
|------|------|----------|
| 推理延迟 | 单次推理耗时 | < 100ms |
| 检测FPS | 每秒检测帧数 | > 5 FPS |
| GPU使用率 | NVIDIA GPU利用率 | 0-100% |
| 检测准确率 | 目标检测准确率 | > 80% |

## 🛠️ 故障排除

### 常见问题

#### 1. 硬件未被检测到
```bash
# 检查Hailo8设备
lspci | grep -i hailo
ls -la /dev/hailo*

# 检查NVIDIA设备
nvidia-smi
lspci | grep -i nvidia
```

#### 2. 服务启动失败
```bash
# 查看服务日志
docker-compose -f docker-compose.zero-config.yml logs -f ai-acceleration-service
docker-compose -f docker-compose.zero-config.yml logs -f frigate

# 重启特定服务
docker-compose -f docker-compose.zero-config.yml restart ai-acceleration-service
```

#### 3. Frigate无法连接AI服务
```bash
# 检查网络连接
docker exec ai-acceleration-service ping frigate
docker exec frigate ping ai-acceleration-service

# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:5000
```

#### 4. 推理失败
```bash
# 手动测试推理接口
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"image": [[[255,0,0]]], "engine": "auto"}' \
  http://localhost:8000/ai/infer

# 查看详细错误日志
docker-compose -f docker-compose.zero-config.yml logs ai-acceleration-service | grep ERROR
```

### 性能优化

#### 调整Frigate检测频率
```yaml
cameras:
  your_camera:
    detect:
      fps: 5          # 降低检测帧率
      max_disappeared: 20  # 减少跟踪时间
```

#### 优化AI推理参数
```yaml
environment:
  - DEFAULT_ENGINE=auto
  - HAILO_BATCH_SIZE=1
  - CUDA_VISIBLE_DEVICES=all
```

## 🔄 维护命令

### 日常维护
```bash
# 查看所有服务状态
docker-compose -f docker-compose.zero-config.yml ps

# 查看实时日志
docker-compose -f docker-compose.zero-config.yml logs -f

# 重启所有服务
docker-compose -f docker-compose.zero-config.yml restart

# 更新服务
docker-compose -f docker-compose.zero-config.yml pull
docker-compose -f docker-compose.zero-config.yml up -d
```

### 清理和维护
```bash
# 停止所有服务
docker-compose -f docker-compose.zero-config.yml down

# 清理未使用的资源
docker system prune -f

# 备份配置
cp config/frigate.yml config/frigate.yml.backup
```

## 🎯 使用场景

### 家庭安防
- 🏠 智能门铃检测
- 🚗 车辆识别
- 👤 人员识别和追踪

### 商业监控
- 🏪 店铺客流分析
- 🚦 停车场管理
- 🔒 安防巡逻

### 工业应用
- 🏭 生产安全监控
- ⚠️ 异常行为检测
- 📊 产量统计

## 📈 扩展部署

### 多节点部署
```bash
# 在多台机器上部署
# 每台机器运行相同的部署脚本
# 通过MQTT共享检测结果
```

### 云端集成
```yaml
# 添加云端存储
environment:
  - FRIGATE_S3_ENDPOINT=your-s3-endpoint
  - FRIGATE_S3_BUCKET=your-bucket
```

## 🎉 总结

通过这个零配置解决方案，您可以：

✅ **5分钟完成部署** - 一键脚本自动完成所有配置
✅ **智能硬件检测** - 自动发现Hailo8和NVIDIA硬件
✅ **无缝Frigate集成** - 自动生成最优配置
✅ **完整监控体系** - Grafana + Prometheus监控面板
✅ **生产级稳定性** - 健康检查、自动重启、日志管理

现在您可以专注于配置摄像头和监控策略，而无需担心底层AI加速硬件的复杂配置！

---

🚀 **开始您的智能监控之旅吧！**