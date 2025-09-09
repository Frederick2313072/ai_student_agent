# 🚀 费曼学习系统 - Vercel官网部署指南

## ⚠️ 重要说明

由于你的项目是一个复杂的AI学习系统，包含ChromaDB、长期运行服务等组件，**完整功能无法直接部署到Vercel**。

本指南提供了一个**简化版本**的部署方案，主要用于：
- API接口测试
- 基础功能验证
- 作为微服务架构中的一个组件

## 📋 部署前准备

### 1. 项目文件检查
确保你的项目根目录包含以下文件：
- ✅ `vercel.json` - Vercel配置文件
- ✅ `api/main.py` - 简化的FastAPI应用
- ✅ `requirements-vercel.txt` - 优化的依赖列表
- ✅ `environments/vercel.env` - 环境变量模板

### 2. 环境变量准备
准备以下环境变量（稍后在Vercel控制台设置）：
```
OPENAI_API_KEY=你的OpenAI密钥
OPENAI_MODEL=gpt-4o-mini
ENVIRONMENT=production
DEBUG=false
SIMPLIFIED_MODE=true
```

## 🌐 Vercel官网部署步骤

### 第1步: 访问Vercel官网
1. 打开 [vercel.com](https://vercel.com)
2. 点击 "Sign Up" 注册账号或 "Log In" 登录
3. 建议使用GitHub账号登录以便连接代码仓库

### 第2步: 连接GitHub仓库
1. 在Vercel控制台点击 "New Project"
2. 选择 "Import Git Repository"
3. 如果是第一次使用，需要授权Vercel访问GitHub
4. 选择你的费曼学习系统仓库

### 第3步: 配置项目设置
1. **Project Name**: 输入项目名称（如 `feynman-learning-api`）
2. **Framework Preset**: 选择 "Other" 或 "Python"
3. **Root Directory**: 保持默认 `./`
4. **Build Command**: 留空（Vercel会自动检测）
5. **Output Directory**: 留空
6. **Install Command**: 使用 `pip install -r requirements-vercel.txt`

### 第4步: 设置环境变量
在 "Environment Variables" 部分添加：

| Name | Value | Environment |
|------|-------|-------------|
| `OPENAI_API_KEY` | 你的OpenAI API密钥 | Production, Preview |
| `OPENAI_MODEL` | `gpt-4o-mini` | Production, Preview |
| `ENVIRONMENT` | `production` | Production |
| `DEBUG` | `false` | Production, Preview |
| `SIMPLIFIED_MODE` | `true` | Production, Preview |

### 第5步: 部署
1. 点击 "Deploy" 开始部署
2. 等待构建完成（通常需要2-5分钟）
3. 部署成功后会获得一个 `.vercel.app` 域名

### 第6步: 验证部署
访问你的部署地址，检查以下端点：
- `https://你的项目.vercel.app/` - 主页
- `https://你的项目.vercel.app/docs` - API文档
- `https://你的项目.vercel.app/health` - 健康检查

## 🔧 故障排除

### 常见问题

1. **构建超时**
   - 原因：依赖包太大
   - 解决：使用 `requirements-vercel.txt` 而不是完整的 `requirements.txt`

2. **函数超时**
   - 原因：AI处理时间过长
   - 解决：将复杂的AI逻辑移到外部服务

3. **包大小限制**
   - 原因：依赖包超过Vercel限制
   - 解决：进一步精简依赖，或使用外部API

4. **环境变量未生效**
   - 检查Vercel控制台中的环境变量设置
   - 确保变量名称完全匹配

### 调试技巧

1. **查看构建日志**
   - 在Vercel控制台的 "Deployments" 页面
   - 点击具体部署查看详细日志

2. **查看函数日志**
   - 在 "Functions" 标签页查看运行时日志
   - 使用 `print()` 语句进行调试

3. **本地测试**
   ```bash
   # 使用简化依赖测试
   pip install -r requirements-vercel.txt
   python api/main.py
   ```

## 🚀 推荐的完整部署架构

由于Vercel的限制，建议采用以下混合架构：

### 架构方案
```
前端 (Streamlit) → Railway/Render
     ↓
API网关 (Vercel) → 简化的API端点
     ↓
AI服务 (Railway/Render) → 完整的AI功能
     ↓
数据库 (Supabase/MongoDB Atlas) → 持久化存储
```

### 推荐平台
1. **完整应用**: Railway、Render、Heroku
2. **AI服务**: Hugging Face Spaces、Modal
3. **数据库**: Supabase、PlanetScale、MongoDB Atlas
4. **前端**: Streamlit Cloud、Netlify

## 📚 下一步

1. **测试简化版API**: 验证基础功能是否正常
2. **部署完整版本**: 考虑使用Railway或Render部署完整功能
3. **设置监控**: 配置错误追踪和性能监控
4. **优化性能**: 根据使用情况调整配置

## 💡 提示

- Vercel更适合前端项目和简单的API
- 复杂的AI应用建议使用专门的平台
- 可以将Vercel作为API网关，后端服务部署在其他平台
- 定期检查Vercel的使用限额，避免超出免费额度

---

如果在部署过程中遇到问题，可以查看Vercel官方文档或在GitHub Issues中反馈。
