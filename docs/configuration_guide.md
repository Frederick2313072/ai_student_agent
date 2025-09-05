# 配置指南 - 费曼学习系统

## 📋 快速配置

### 基础启动（最小配置）
```bash
# 1. 复制环境变量模板
cp environments/test.env environments/local.env

# 2. 编辑配置文件，设置必需的API密钥
# 必需：OPENAI_API_KEY 或 ZHIPU_API_KEY
# 可选：其他第三方API密钥

# 3. 启动应用
uv run python run_app.py
```

## 🔑 环境变量配置详解

### 核心配置 (必需)

#### LLM模型配置
```env
# OpenAI配置 (推荐)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=""  # 可选，用于代理或自定义端点

# 或使用智谱AI
ZHIPU_API_KEY="your-key.your-secret"
ZHIPU_MODEL=glm-4.5-airx
```

### 功能增强配置 (可选)

#### 搜索工具
```env
# 网络搜索 (推荐)
TAVILY_API_KEY="your-tavily-key"

# 视频搜索
YOUTUBE_API_KEY="your-youtube-api-key" 

# 新闻搜索
NEWS_API_KEY="your-newsapi-key"
```

#### 多媒体工具
```env
# 翻译功能
BAIDU_TRANSLATE_API_KEY="your-baidu-key"
BAIDU_TRANSLATE_SECRET_KEY="your-baidu-secret"

# 数学计算
WOLFRAM_API_KEY="your-wolfram-key"

# 代码执行
JUDGE0_API_KEY="your-judge0-key"

# 高级图表 (可选)
QUICKCHART_API_KEY="your-quickchart-key"
```

#### 监控追踪
```env
# 基础监控
MONITORING_ENABLED=true
METRICS_ENABLED=true

# LLM追踪 (推荐)
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST=https://cloud.langfuse.com

# 分布式追踪 (高级)
TRACING_ENABLED=true
OTEL_SERVICE_NAME=feynman-learning-system
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## 🌍 环境区分

### 开发环境 (development)
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
API_RELOAD=true
CORS_ORIGINS=["*"]
```

### 生产环境 (production)
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_RELOAD=false
CORS_ORIGINS=["https://your-domain.com"]
REQUEST_TIMEOUT_SECONDS=60
MAX_REQUEST_SIZE_BYTES=5242880
```

## 🔧 配置验证

### 自动检查配置
```bash
# 检查配置完整性
uv run python -c "
import sys; sys.path.insert(0, 'src')
from feynman.core.config.settings import validate_configuration
validate_configuration()
"
```

### 手动检查关键配置
```bash
# 检查LLM配置
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv('environments/test.env')
print('OpenAI Key:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')
print('Zhipu Key:', '✅' if os.getenv('ZHIPU_API_KEY') else '❌')
"
```

## 📊 监控配置

### Docker监控栈
```bash
# 启动监控组件
docker-compose -f config/docker-compose.monitoring.yml up -d

# 访问监控面板
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
```

### 成本控制
```env
# 设置成本限制
DAILY_COST_LIMIT_USD=50
MONTHLY_COST_LIMIT_USD=500
COST_TRACKING_ENABLED=true
TOKEN_RATE_LIMIT=5000
```

## 🚨 故障排除

### 常见问题

#### 1. 应用启动失败
```bash
# 检查依赖
uv sync

# 检查配置
uv run python -c "from dotenv import load_dotenv; load_dotenv('environments/test.env'); import os; print('配置已加载')"
```

#### 2. 工具功能受限
- **原因**: 对应API密钥未设置
- **解决**: 检查 `environments/test.env` 中的API密钥配置
- **降级**: 大部分工具支持降级模式，不会影响核心功能

#### 3. 监控不工作
```bash
# 检查监控配置
grep -E "MONITORING_|TRACING_|LANGFUSE_" environments/test.env
```

#### 4. 向量数据库错误
```bash
# 检查ChromaDB目录
ls -la chroma_db/ || mkdir -p chroma_db
```

## 📝 配置模板

### 最小化配置模板
```env
# environments/minimal.env
ENVIRONMENT=development
OPENAI_API_KEY="your-openai-key"
MONITORING_ENABLED=false
DEBUG=true
```

### 完整功能配置模板
```env
# environments/full.env  
ENVIRONMENT=development
OPENAI_API_KEY="your-openai-key"
TAVILY_API_KEY="your-tavily-key"
BAIDU_TRANSLATE_API_KEY="your-baidu-key"
BAIDU_TRANSLATE_SECRET_KEY="your-baidu-secret"
MONITORING_ENABLED=true
LANGFUSE_PUBLIC_KEY="your-langfuse-public"
LANGFUSE_SECRET_KEY="your-langfuse-secret"
```

### 生产环境配置模板
```env
# environments/production.env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
OPENAI_API_KEY="your-production-openai-key"
CORS_ORIGINS=["https://your-app.com"]
DAILY_COST_LIMIT_USD=100
MONITORING_ENABLED=true
TRACING_ENABLED=true
```

## 🔐 安全配置建议

1. **API密钥管理**
   - 使用环境变量，永远不要硬编码
   - 定期轮换API密钥
   - 使用不同密钥用于开发/生产环境

2. **访问控制**
   - 生产环境严格设置CORS来源
   - 启用请求大小和超时限制
   - 配置适当的日志级别

3. **成本控制**
   - 设置每日/月度成本限制
   - 启用Token使用监控
   - 配置告警阈值

## 🔄 配置热重载

修改环境变量后需要重启应用：
```bash
# 开发环境 (自动重载)
uv run python run_app.py

# 生产环境 (手动重启)
pkill -f "uvicorn" && uv run uvicorn main:app --host 0.0.0.0 --port 8000
```
