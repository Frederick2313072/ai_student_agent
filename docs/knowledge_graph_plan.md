## 知识图谱构建与可视化实施计划

### 目标
- 从用户输入与本地文档中抽取结构化知识（三元组），构建主题可检索的知识图谱
- 提供查询、统计、子图提取等API
- 在 Streamlit 中进行交互式可视化，并支持按主题/节点筛选

### 总体方案
- 数据流：文本/对话 → 实体与关系抽取 → 三元组去重/合并 → 入库（本地或Neo4j）→ API检索 → 可视化

```mermaid
flowchart LR
  A[文本/对话] --> B[实体/关系抽取]
  B --> C[三元组(去重/合并)]
  C --> D{存储}
  D -->|本地| E[NetworkX/JSON]
  D -->|图数据库| F[Neo4j]
  E --> G[API检索]
  F --> G
  G --> H[Streamlit 可视化]
```

### 模块改动清单
1) 依赖
- 新增（计划）：`networkx`, `pyvis` 或 `plotly`, 可选 `neo4j`/`py2neo`, `spacy`, `spacy-transformers`（或基于LLM的抽取链）
- `requirements.txt` 与 `pyproject.toml` 添加上述依赖（按选择的实现逐步加入）

2) 新增 `core/graph/` 模块
- `core/graph/schema.py`：节点与边的数据模型定义（pydantic），三元组结构 `(subject, predicate, object)`
- `core/graph/extractor.py`：
  - 抽取管线：支持 LLM 抽取（优先）与 spaCy 规则/NER 作为兜底
  - 输入：原始文本；输出：去重后的三元组列表
- `core/graph/storage.py`：
  - 本地后端：NetworkX 图与JSON持久化（最小可用）
  - 可选后端：Neo4j（读写、去重、索引、基本统计），通过环境变量开关
- `core/graph/builder.py`：
  - 高层封装：三元组→图构建、合并、去重策略（同义词合并可后续迭代）
- `core/graph/service.py`：
  - 供API/Agent调用的服务层：`build_from_text`、`build_from_file`、`query_graph`、`subgraph(center, radius)`、`stats()`

3) 修改 `ingest.py`
- 可选钩子：在完成RAG向量化后，调用 `core/graph/service.py` 对同一文档进行知识图谱抽取与入库
- 增加命令行参数：`--build-kg` 开关

4) 修改 `agent/tools.py`
- 新增工具 `graph_query`：允许 Agent 在提问前查询图谱节点/关系，生成更有针对性的问题或引用
- 新增工具 `graph_explain`（可选）：给定节点，返回其一阶/二阶邻接关系摘要

5) 修改 `main.py`（或重建路由至 `api/routers/graph.py`）
- 新增API：
  - `POST /kg/build`：入参 `text` 或 `file_path`，触发抽取与入库
  - `GET /kg/graph`：返回全图/按主题过滤后的图（JSON，含节点与边）
  - `GET /kg/subgraph`：参数 `center`, `radius`
  - `GET /kg/stats`：节点数、边数、度分布概要

6) 修改 `ui.py`（Streamlit 可视化）
- 新增侧边栏：知识图谱开关/过滤条件（主题、关键节点、半径）
- 新增页签：
  - 图谱查看：使用 `pyvis` 或 `plotly` 渲染交互式图（力导向/层次布局）
  - 节点详情：点击节点显示属性、关联三元组与相关文档片段

7) 测试用例 `tests/`
- 单元：
  - 抽取器：保证给定样本文本可抽取稳定三元组集合
  - 存储层：去重与合并逻辑、JSON/Neo4j 读写
- 集成：
  - `/kg/build`、`/kg/graph`、`/kg/subgraph` API连通性与数据契约

### 环境变量规划
- `KG_BACKEND`：`local` 或 `neo4j`
- `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`（启用Neo4j时必填）
- `KG_MAX_NODES`、`KG_MAX_EDGES`（可选：限制返回量）

### API 契约草案
- `POST /kg/build`
  - 请求：`{"text": "..."}` 或 `{"file_path": "data/xxx.txt"}`
  - 响应：`{"triples": [...], "nodes": n, "edges": m}`
- `GET /kg/graph?topic=Python&limit=1000`
  - 响应：`{"nodes": [...], "edges": [...]}`
- `GET /kg/subgraph?center=GIL&radius=2`
  - 响应：同上（子图）
- `GET /kg/stats`
  - 响应：`{"num_nodes": n, "num_edges": m, "degree": {"p50":..., "p95":...}}`

### 可视化方案对比
- `pyvis`：快速渲染、交互较好、可导出HTML，适合Streamlit嵌入
- `plotly`：与数据分析生态融合，定制力导向/弦图需额外封装
- Next.js 前端（可选扩展）：`Cytoscape.js`/`vis-network` + `/kg` API

### 里程碑与工作量
- M0（0.5d）：依赖与目录初始化，环境变量与开关
- M1（2d）：抽取器最小可用（LLM链 + 规则兜底），三元组去重与合并
- M2（1.5d）：本地存储（NetworkX/JSON），基础统计
- M3（1d）：FastAPI `/kg/*` 路由与契约实现
- M4（1.5d）：Streamlit 可视化（pyvis 集成、筛选器、节点详情）
- M5（1d）：Agent 工具 `graph_query` 集成与回归验证
- M6（1d）：测试用例完善与文档更新

### 验收标准
- 给定样本文本，能够稳定抽取≥80% 关键三元组
- `/kg/*` API 在10k节点/50k边量级下可正常查询（本地后端）
- Streamlit 中能按主题/节点筛选并交互查看
- Agent 能调用 `graph_query` 并将结果用于追问或解释

### 风险与回滚
- LLM 抽取稳定性：提供 spaCy 兜底与后处理（正则/模式）
- 数据规模：默认本地存储，达到阈值再切换 Neo4j（开关与迁移工具）
- 可视化性能：返回数据量限流，子图与分页加载

### 开发顺序建议
1. 先本地后端（NetworkX/JSON）+ 最小可视化闭环
2. 稳定抽取质量与三元组合并
3. 再接 Neo4j 与前端增强


