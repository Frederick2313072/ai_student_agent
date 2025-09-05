# 🧪 Celery + Redis 完整测试指南

## 📋 测试环境启动步骤

### 第一步：开启三个终端窗口

#### 🔥 终端 1 - 启动 Celery Worker
```bash
cd /Users/frederick/Documents/ai_student_agent
make celery-worker
```

**预期输出：**
```
🚀 启动 Celery Worker...
 -------------- celery@hostname v5.5.3
---- **** ----- 
--- * ***  * -- Darwin
-- * - **** --- 
- ** ---------- 

[config]
.> app:         feynman_tasks:0x...
.> transport:   redis://default:***@redis-cloud.com:18491//
.> results:     redis://default:***@redis-cloud.com:18491//
.> concurrency: 2 (prefork)

[queues]
.> default          exchange=default(direct) key=default
.> memory           exchange=memory(direct) key=memory
.> knowledge        exchange=knowledge(direct) key=knowledge
.> monitoring       exchange=monitoring(direct) key=monitoring

[2025-01-23 10:00:00,000: INFO/MainProcess] Connected to redis://...
[2025-01-23 10:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-01-23 10:00:01,000: INFO/MainProcess] mingle: all alone
[2025-01-23 10:00:01,000: INFO/MainProcess] Ready to receive tasks!
```

#### 🌸 终端 2 - 启动 Flower 监控面板
```bash
cd /Users/frederick/Documents/ai_student_agent
make celery-flower
```

**预期输出：**
```
🌸 启动 Flower 监控面板...
[I 250123 10:00:00 command:140] Starting flower...
[I 250123 10:00:00 mixins:231] Connected to redis://...
[I 250123 10:00:00 web:2349] Flower is running on http://127.0.0.1:5555
```

**访问监控面板：** http://localhost:5555

#### 🌐 终端 3 - 启动 API 服务
```bash
cd /Users/frederick/Documents/ai_student_agent
make run
```

**预期输出：**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 📤 第二步：测试任务提交和执行

### 方法1：通过 Python 脚本测试
```bash
# 在新终端窗口中运行
cd /Users/frederick/Documents/ai_student_agent
uv run python scripts/test_celery.py
```

**预期结果：**
- ✅ Redis连接成功
- ✅ 任务提交成功
- ✅ 发现活跃的Worker
- ✅ 任务执行完成

### 方法2：通过 API 端点测试
```bash
# 测试记忆固化 API
curl -X POST "http://localhost:8000/memorize" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "测试主题",
    "conversation_history": [
      {"role": "user", "content": "这是一个测试消息"},
      {"role": "assistant", "content": "我收到了测试消息"}
    ]
  }'
```

**预期响应：**
```json
{
  "message": "记忆任务已加入Celery队列处理。",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "submitted"
}
```

### 方法3：查询任务状态
```bash
# 使用上面返回的 task_id
curl -X GET "http://localhost:8000/task/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**预期响应（执行中）：**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PROGRESS",
  "current": 50,
  "message": "正在生成摘要..."
}
```

**预期响应（完成）：**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "current": 100,
  "message": "任务执行成功",
  "result": {
    "status": "success",
    "topic": "测试主题",
    "message": "记忆固化任务成功完成"
  }
}
```

## 📊 第三步：监控任务执行

### 1. Flower 监控面板
访问 http://localhost:5555，你将看到：

- **Tasks** 页面：所有任务的执行历史和状态
- **Workers** 页面：Worker 的运行状态和统计信息
- **Monitor** 页面：实时任务执行监控
- **Broker** 页面：Redis 队列状态

### 2. 命令行监控
```bash
# 查看 Worker 状态
make celery-status

# 查看活跃任务
make celery-inspect

# 查看队列统计
uv run celery -A feynman.tasks.celery_app.celery_app inspect stats
```

## 🧪 第四步：压力测试

### 批量提交任务测试
```bash
# 提交多个任务测试并发处理
for i in {1..10}; do
  curl -X POST "http://localhost:8000/memorize" \
    -H "Content-Type: application/json" \
    -d "{
      \"topic\": \"压力测试主题$i\",
      \"conversation_history\": [
        {\"role\": \"user\", \"content\": \"压力测试消息$i\"},
        {\"role\": \"assistant\", \"content\": \"收到压力测试消息$i\"}
      ]
    }" &
done
wait
echo "所有任务已提交"
```

### 验证任务处理
在 Flower 监控面板中观察：
- 任务提交速度
- Worker 处理能力
- 队列积压情况
- 成功/失败统计

## 🔧 故障排查

### 常见问题及解决方案

#### 1. Worker 启动失败
**症状：** `redis.exceptions.ConnectionError`
**解决：** 检查 Redis 配置和网络连接
```bash
# 验证 Redis 连接
uv run python -c "
import redis, os
from dotenv import load_dotenv
load_dotenv('environments/test.env')
r = redis.from_url(os.getenv('REDIS_URL'))
print('Redis连接:', '✅ 成功' if r.ping() else '❌ 失败')
"
```

#### 2. 任务卡住不执行
**症状：** 任务状态一直是 PENDING
**解决：** 检查 Worker 是否运行
```bash
make celery-status
```

#### 3. Flower 无法连接
**症状：** `Broker connection error`
**解决：** 确保 Redis URL 配置正确
```bash
# 检查环境变量
echo $REDIS_URL
```

#### 4. API 调用超时
**症状：** `Connection timeout`
**解决：** 检查 API 服务是否运行
```bash
curl -X GET "http://localhost:8000/docs"
```

## ✅ 测试成功标准

当你看到以下所有指标都正常时，说明测试成功：

### Worker 指标
- ✅ Worker 状态：ONLINE
- ✅ 处理任务数：> 0
- ✅ 失败任务数：= 0

### Redis 指标  
- ✅ 连接状态：Connected
- ✅ 内存使用：正常
- ✅ 队列长度：处理及时

### API 指标
- ✅ 响应时间：< 200ms
- ✅ 任务提交：成功
- ✅ 状态查询：正常

### Flower 监控
- ✅ 能正常访问监控面板
- ✅ 实时显示任务状态
- ✅ Worker 统计正常

恭喜！🎉 你的 Celery + Redis 任务队列系统已经完全正常工作！


