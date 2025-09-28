# 🎓 AI学生费曼学习系统 (V3)

一个基于 **LangGraph** 和 **FastAPI** 的高级AI Agent，它扮演"AI学生"的角色，通过费曼学习法帮助用户巩固和深化知识。

> **最新更新**: 系统已完成重构，采用模块化架构，支持多种工具集成和异步处理。

## 🌟 项目特色

- **🤖 ReAct Agent核心**: 使用能够**思考**和**行动**的智能体，而不仅仅是问答。
- **🚀 流式响应**: Agent的回答以打字机效果实时显示，提升了交互的即时感和用户体验。
- **🛠️ 可扩展工具集**: Agent可以使用多种工具来辅助分析：
    - **网络搜索**: 验证信息，获取最新知识 (Tavily)。
    - **图像搜索**: 进行多模态的图片检索 (SerpApi)。
    - **知识库检索 (RAG)**: 从您提供的本地文档中检索相关信息。
    - **长期记忆**: 回忆过去的对话，实现上下文关联。
- **🚀 微服务架构**: 主要功能（如图像搜索）被构建为独立的FastAPI服务，易于维护和扩展。
- **🧠 长期与短期记忆**: 区分会话内的短期记忆和跨会话的长期记忆（存储于ChromaDB）。
- **🖥️ 交互式Web界面**: 提供基于Streamlit的友好界面，方便与Agent进行对话。
- **✅ 异步处理**: 基于FastAPI和LangGraph的异步能力，实现高效的请求处理。

## 🏗️ 技术架构

- **核心框架**: LangGraph, LangChain
- **后端服务**: FastAPI
- **Web界面**: Streamlit
- **向量数据库**: ChromaDB
- **工具API**: Tavily (网络搜索), SerpApi (图像搜索)

### 系统架构图

```mermaid
graph TD
    subgraph "用户端"
        UI(🖥️ Streamlit UI)
    end

    subgraph "主应用 (main.py)"
        API(🚀 FastAPI API)
    end

    subgraph "Agent核心 (agent/)"
        LG[🧠 LangGraph 工作流]
        React(🤖 ReAct Agent)
    end
    
    subgraph "工具集 (tools/)"
        Tavily(🌐 网络搜索)
        RAG(📚 知识库检索)
        Memory(💾 记忆检索)
        ImageSearchTool(🖼️ 图像搜索工具)
    end
    
    subgraph "外部依赖"
        Chroma(🗄️ ChromaDB)
        MCP(🛰️ 图像搜索微服务)
    end

    UI -- HTTP Request --> API
    API -- 调用 --> LG
    LG -- 驱动 --> React
    React -- 使用 --> Tavily
    React -- 使用 --> RAG
    React -- 使用 --> Memory
    React -- 使用 --> ImageSearchTool
    ImageSearchTool -- HTTP Request --> MCP
    RAG -- 查询 --> Chroma
    Memory -- 查询 --> Chroma
```

## 🚀 快速开始（开发环境）

### 1) 安装依赖
```bash
uv sync
```

### 2) 配置环境
```bash
cp env_template .env
# 打开 .env，至少设置：
# OPENAI_API_KEY=你的key（或设置 ZHIPU_API_KEY）
# REDIS_URL=redis://localhost:6379  # 如使用本地Redis
```

### 3) 启动服务（推荐一键）
```bash
./scripts/restart_all.sh start     # 启动后端API + 前端 + Celery + Flower（如可用）
```

或手动启动（两个终端）：
```bash
# 终端1：后端API
uv run uvicorn main:app --reload --port 8005

# 终端2：前端
uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py --server.port 8501
```

### 4) 访问
- 前端：`http://localhost:8501`
- API 文档：`http://localhost:8005/docs`

### 5) 重启/停止
```bash
./scripts/restart_all.sh           # 重启全部
./scripts/restart_all.sh stop      # 停止全部
./scripts/restart_all.sh start     # 启动全部
```

## 📖 API 使用（核心）

应用后端是一个标准的FastAPI服务。你可以在服务启动后，访问 `http://localhost:8005/docs` 查看并测试API接口。

- **核心端点**: 
  - `POST /api/v1/chat/stream`：(推荐) SSE 流式对话
  - `POST /api/v1/chat`：一次性返回
  - `POST /api/v1/chat/memorize`：提交记忆固化（自动降级）
- **请求体 (`/chat/stream`)**:
  ```json
  {
    "topic": "string",
    "explanation": "string",
    "session_id": "string",
    "short_term_memory": [
      {
        "role": "string",
        "content": "string"
      }
    ]
  }
  ```

## 🔧 开发与测试（简要）
```bash
uv run pytest
```

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**
   - 确保端口 8005,8501 未被占用
   - 可以修改启动命令中的端口号

2. **API密钥问题**
   - 确保 `environments/test.env` 中的 OpenAI API 密钥有效
   - 检查网络连接和API配额

3. **依赖安装问题**
   - 使用虚拟环境避免依赖冲突
   - 确保Python版本为3.9+

4. **服务启动失败**
   - 检查日志输出中的错误信息
   - 确保所有必需的环境变量已设置

### 获取帮助

- 查看 `logs/` 目录中的日志文件
- 检查 FastAPI 自动生成的文档: `http://localhost:8005/docs`
- 提交 GitHub Issues 报告问题

## 📁 项目结构说明

```
ai_student_agent/
├── src/                          # 源码根目录
│   ├── feynman/                  # 主要应用包
│   │   ├── agents/               # AI代理核心逻辑
│   │   │   ├── core/             # 代理核心实现
│   │   │   ├── parsers/          # 响应解析器
│   │   │   └── tools/            # 工具集成
│   │   ├── api/                  # API路由和处理器
│   │   ├── core/                 # 核心组件
│   │   │   ├── config/           # 配置管理
│   │   │   └── graph/            # LangGraph工作流
│   │   ├── infrastructure/       # 基础设施层
│   │   ├── interfaces/           # 接口层
│   │   │   └── web/              # Web接口实现
│   │   └── tasks/                # 异步任务处理
│   └── main.py                   # FastAPI应用入口
├── config/                       # 配置目录
│   ├── alerting_rules.yml        # Prometheus告警规则
│   ├── alertmanager.yml          # Alertmanager配置
│   ├── blackbox.yml              # 黑盒监控配置
│   ├── docker-compose.monitoring.yml # 监控栈配置
│   ├── grafana/                  # Grafana仪表板配置
│   ├── nginx/                    # Nginx反向代理配置
│   └── prometheus.yml            # Prometheus配置
├── scripts/                      # 部署和管理脚本
│   ├── development/              # 开发环境脚本
│   │   └── deploy_feynman_app.sh # 完整部署脚本
│   ├── setup/                    # 环境设置脚本
│   └── monitoring/               # 监控相关脚本
├── webapp/                       # 前端Web应用
│   ├── src/                      # 前端源码
│   ├── package.json              # Node.js依赖
│   ├── vite.config.ts            # Vite构建配置
│   └── index.html                # 应用入口
├── docs/                         # 项目文档
│   ├── architecture_refactoring_summary.md
│   ├── multi_agent_system_implementation_summary.md
│   └── project_structure.md      # 项目结构详细说明
├── examples/                     # 示例代码和演示
│   ├── advanced/                 # 高级用法示例
│   ├── knowledge_graph_demo.py   # 知识图谱演示
│   └── simple_kg_test.py         # 简单知识图谱测试
├── storage/                      # 持久化存储
│   └── logs/                     # 结构化日志存储
├── chroma_db/                    # ChromaDB向量数据库
├── data/                         # 知识库数据文件
├── logs/                         # 应用运行日志
├── tests/                        # 测试代码
│   └── integration/              # 集成测试
├── pyproject.toml                # Python项目配置
├── uv.lock                       # 依赖版本锁定
├── env_template                  # 环境变量配置模板
└── README.md                     # 项目文档
```

## 📋 版本信息

### 当前版本: V3.2
- ✅ 基于 LangGraph 的 ReAct Agent 架构
- ✅ 支持多种工具集成（网络搜索、翻译、数学计算、学术检索等）
- ✅ 流式响应与打字机UI效果
- ✅ 记忆固化移至后台任务，API响应更快
- ✅ 长短期记忆管理
- ✅ 异步 FastAPI 后端
- ✅ Streamlit Web 界面
- ✅ **服务器部署支持**
  - nginx反向代理配置
  - systemd服务管理
  - 域名访问支持 (feynmanlearning.wiki)
  - WebSocket连接优化
- ✅ 完整的监控与追踪系统
  - OpenTelemetry 分布式追踪
  - Prometheus 指标收集
  - 结构化日志记录
  - LLM 成本追踪和预算控制
  - 健康检查和告警系统
  - Grafana 可视化面板

### 主要依赖
- **Python**: 3.9+
- **LangChain**: 最新版本
- **LangGraph**: 工作流引擎
- **FastAPI**: Web 框架
- **Streamlit**: 前端界面
- **ChromaDB**: 向量数据库
- **OpenAI**: GPT 模型

### 更新日志
- **V3.0**: 完全重构，采用 LangGraph 架构，新增流式输出, 优化UI渲染, 改进启动流程, 增加后台记忆任务
- **V2.x**: 多智能体系统（已废弃）
- **V1.x**: 基础费曼学习实现（已废弃）

---

**通过向AI学生教授来真正掌握知识！** 🚀

*基于费曼学习法的原理：教授他人是最好的学习方式。* 