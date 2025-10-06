# AI加速引擎选择指南

## 🎯 概述

增强版AI加速服务支持多种引擎选择策略，可以根据您的具体需求灵活调用Hailo8和NVIDIA GPU硬件资源。

## 🔧 引擎类型详解

### 1. `auto` - 自动选择 (推荐)
**适用场景**: 通用场景，希望系统自动优化

**工作原理**:
- 系统自动检测可用硬件
- 如果两个引擎都可用，使用负载均衡策略
- 优先考虑性能和资源利用率的平衡

**优势**:
- 无需手动配置
- 自动适应不同负载情况
- 最佳的性能/资源比

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "auto",
    "priority": "performance"
  }' \
  http://localhost:8000/ai/infer
```

---

### 2. `hailo` - 仅使用Hailo8
**适用场景**:
- 边缘计算场景
- 低功耗需求
- 实时性要求高
- 成本敏感的应用

**优势**:
- 功耗低 (约15-25W)
- 延迟稳定 (通常<10ms)
- 专门优化的AI推理
- 成本效益高

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "hailo",
    "threshold": 0.5
  }' \
  http://localhost:8000/ai/infer
```

---

### 3. `nvidia` - 仅使用NVIDIA GPU
**适用场景**:
- 高精度要求
- 复杂模型推理
- 批量处理
- 研究和开发

**优势**:
- 高计算性能
- 支持复杂模型
- 软件生态丰富
- 灵活性高

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "nvidia",
    "priority": "accuracy"
  }' \
  http://localhost:8000/ai/infer
```

---

### 4. `both` - 双引擎融合
**适用场景**:
- 高精度要求的关键应用
- 安全监控
- 医疗影像分析
- 金融风控

**工作原理**:
- 同时使用两个引擎进行推理
- 智能融合两个引擎的结果
- 根据优先级选择最佳融合策略

**融合策略**:
- **accuracy优先**: 选择置信度更高的结果
- **latency优先**: 选择响应更快的结果
- **performance优先**: 融合两个结果提高检测质量

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "both",
    "priority": "accuracy",
    "threshold": 0.3
  }' \
  http://localhost:8000/ai/infer
```

---

### 5. `parallel` - 并行推理
**适用场景**:
- 高吞吐量需求
- 实时视频流处理
- 大规模图像处理
- 性能基准测试

**工作原理**:
- 同时启动两个引擎的推理任务
- 等待所有任务完成后合并结果
- 总处理时间取决于较慢的引擎

**优势**:
- 最大化硬件利用率
- 提高系统吞吐量
- 获得更全面的检测结果

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "parallel",
    "timeout": 15.0
  }' \
  http://localhost:8000/ai/infer
```

---

### 6. `load_balance` - 负载均衡
**适用场景**:
- 长时间运行的推理服务
- 变化的负载模式
- 多用户并发访问
- 生产环境部署

**工作原理**:
- 基于历史性能数据动态调整权重
- 考虑当前负载情况
- 自动优化资源分配

**优势**:
- 自动适应负载变化
- 避免单一硬件过载
- 提高系统稳定性

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "load_balance",
    "priority": "performance"
  }' \
  http://localhost:8000/ai/infer
```

## 📊 性能对比

| 引擎模式 | 延迟 | 吞吐量 | 精度 | 功耗 | 适用场景 |
|---------|------|--------|------|------|----------|
| hailo | 低 (5-10ms) | 中 | 中 | 低 (15-25W) | 边缘实时推理 |
| nvidia | 中 (20-50ms) | 高 | 高 | 高 (200-350W) | 高精度复杂推理 |
| both | 高 (30-60ms) | 中 | 最高 | 中高 (220-375W) | 高精度关键应用 |
| parallel | 高 (25-55ms) | 最高 | 中高 | 高 (220-375W) | 高吞吐量场景 |
| load_balance | 中低 (8-30ms) | 中高 | 中高 | 中 (变化) | 生产环境 |

## 🎛️ 高级配置

### 优先级设置

```json
{
  "priority": "performance"  // performance/latency/accuracy
}
```

- **performance**: 平衡性能和精度
- **latency**: 优先考虑响应速度
- **accuracy**: 优先考虑检测精度

### 超时设置

```json
{
  "timeout": 10.0  // 超时时间(秒)
}
```

不同模式的建议超时时间：
- `hailo`: 5-10秒
- `nvidia`: 10-20秒
- `both`: 15-30秒
- `parallel`: 15-25秒
- `load_balance`: 10-20秒

### 结果数量限制

```json
{
  "max_results": 100  // 最大返回结果数
}
```

## 🔍 实际应用示例

### 示例1: 智能摄像头系统
```yaml
# 边缘摄像头 - 使用Hailo8
{
  "engine": "hailo",
  "priority": "latency",
  "threshold": 0.6
}

# 中央服务器 - 使用负载均衡
{
  "engine": "load_balance",
  "priority": "performance",
  "threshold": 0.4
}
```

### 示例2: 安防监控系统
```yaml
# 实时报警 - 使用Hailo8
{
  "engine": "hailo",
  "priority": "latency",
  "timeout": 5.0
}

# 事后分析 - 使用双引擎融合
{
  "engine": "both",
  "priority": "accuracy",
  "threshold": 0.2,
  "timeout": 30.0
}
```

### 示例3: 批量图像处理
```yaml
# 高吞吐量处理
{
  "engine": "parallel",
  "priority": "performance",
  "max_results": 50,
  "timeout": 20.0
}
```

## 📈 性能监控

### 获取引擎信息
```bash
curl http://localhost:8000/ai/engines
```

### 查看实时性能
```bash
curl http://localhost:8000/ai/health
```

### 监控负载均衡状态
```bash
curl http://localhost:8000/ai/hardware
```

## 🚨 注意事项

### 1. 硬件要求
- `both`, `parallel`, `load_balance` 模式需要两个硬件都可用
- 确保硬件驱动正确安装和配置

### 2. 资源管理
- 并行模式会消耗更多内存和计算资源
- 监控GPU温度和内存使用情况

### 3. 网络延迟
- 远程调用时考虑网络延迟影响
- 合理设置超时时间

### 4. 模型兼容性
- 确保模型在两个硬件上都能正常运行
- 注意不同硬件的精度差异

## 🎯 最佳实践

1. **开发阶段**: 使用 `auto` 模式快速验证功能
2. **测试阶段**: 使用 `both` 模式验证检测精度
3. **生产部署**: 根据具体需求选择合适的引擎模式
4. **性能调优**: 定期监控和调整引擎配置
5. **故障处理**: 设置合适的超时和错误处理机制

通过合理选择引擎模式，您可以在性能、精度、功耗和成本之间找到最佳平衡点。