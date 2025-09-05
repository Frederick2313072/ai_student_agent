# 环境配置目录

本目录包含费曼学习系统的所有环境变量配置文件。

## 📁 配置文件说明

### 主要配置文件
- `test.env` - 主配置文件，包含所有可用的配置选项
- `development.env` - 开发环境优化配置
- `production.env` - 生产环境安全配置
- `minimal.env` - 最小功能配置

### 使用方法

#### 1. 快速开始
```bash
# 复制主配置文件
cp environments/test.env environments/local.env

# 编辑配置文件，设置必需的API密钥
vim environments/local.env

# 验证配置
make config-check
```

#### 2. 创建特定环境配置
```bash
# 创建开发环境配置
make config-dev

# 创建生产环境配置
make config-prod

# 创建最小配置
make config-minimal
```

#### 3. 交互式配置设置
```bash
make config-setup
```

## 🔑 必需配置项

### LLM模型 (必需其一)
```env
# OpenAI (推荐)
OPENAI_API_KEY="sk-..."

# 或智谱AI
ZHIPU_API_KEY="your-key.your-secret"
```

### 可选功能配置
```env
# 网络搜索 (推荐)
TAVILY_API_KEY="your-tavily-key"

# 翻译功能
BAIDU_TRANSLATE_API_KEY="your-baidu-key"
BAIDU_TRANSLATE_SECRET_KEY="your-baidu-secret"

# 监控追踪 (推荐)
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
```

## 🛡️ 安全建议

1. **永远不要提交包含真实API密钥的.env文件**
2. **使用不同的API密钥用于开发和生产环境**
3. **定期轮换API密钥**
4. **生产环境使用严格的CORS配置**

## 🔧 故障排除

### 配置验证失败
```bash
# 检查配置完整性
python scripts/config_validator.py

# 查看详细的设置指南
python scripts/config_validator.py --show-guide
```

### 应用启动失败
```bash
# 完整的开发环境检查
make dev-check

# 测试关键模块导入
python scripts/dev_helper.py check
```

## 📝 配置模板

参考 `test.env` 获取完整的配置选项列表和说明。
