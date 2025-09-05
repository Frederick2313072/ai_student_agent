# 真实知识抽取和图谱构建实战指南

## 🎯 概述

本指南演示如何使用费曼学习系统处理真实文本数据，进行知识抽取和知识图谱构建。通过实际案例展示完整的工作流程和最佳实践。

## 📊 演示结果总结

### 处理的文本数据
- **AI/ML文章** (1,462字符): 抽取40个三元组
- **科学发现文章** (1,285字符): 抽取27个三元组  
- **教育理论文章** (1,552字符): 抽取32个三元组

### 构建的知识图谱
- **总规模**: 99个三元组，141个节点，119条边
- **关系类型**: 50+种语义关系（如"是"、"用于"、"属于"、"基于"等）
- **连通性**: 29个连通组件，最大组件24个节点
- **重要实体**: Python(度数9)、费曼学习法(度数9)、机器学习(度数7)

---

## 🚀 使用流程

### 步骤1: 准备文本数据

```bash
# 创建文本文件目录
mkdir -p data/sample_texts

# 准备不同领域的文本文件
# - data/sample_texts/ai_ml_article.txt
# - data/sample_texts/science_discovery.txt  
# - data/sample_texts/education_theory.txt
```

**文本质量要求**:
- 结构化的段落和句子
- 明确的概念定义和关系表述
- 避免过多的口语化表达
- 每个文档建议1000-3000字符

### 步骤2: 启动知识抽取服务

```bash
# 方法1: 使用Make命令（推荐）
make run

# 方法2: 直接启动
cd src && uv run python main.py

# 验证服务状态
curl http://127.0.0.1:8000/health
```

**服务配置**:
- API地址: `http://127.0.0.1:8000`
- 文档地址: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/health`

### 步骤3: 知识图谱构建

#### 3.1 从文本构建

```bash
# API调用示例
curl -X POST http://127.0.0.1:8000/api/v1/kg/build \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你的文本内容",
    "source": "文档来源标识"
  }'
```

#### 3.2 从文件构建

```bash
curl -X POST http://127.0.0.1:8000/api/v1/kg/build \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/sample_texts/ai_ml_article.txt",
    "source": "ai_article"
  }'
```

#### 3.3 批量处理脚本

```python
import requests
import os

def build_kg_from_texts(text_dir, api_url="http://127.0.0.1:8000"):
    for filename in os.listdir(text_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(text_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            response = requests.post(f"{api_url}/api/v1/kg/build", 
                json={
                    "text": text,
                    "source": filename.replace('.txt', '')
                }
            )
            print(f"处理 {filename}: {response.json()}")

# 使用示例
build_kg_from_texts("data/sample_texts")
```

---

## 🔍 图谱查询和分析

### 4.1 基础查询

```bash
# 获取图谱统计信息
curl http://127.0.0.1:8000/api/v1/kg/stats

# 搜索特定实体
curl "http://127.0.0.1:8000/api/v1/kg/search?query=Python&limit=5"

# 查看实体邻居
curl "http://127.0.0.1:8000/api/v1/kg/neighbors?entity=Python"

# 获取子图
curl "http://127.0.0.1:8000/api/v1/kg/subgraph?center=Python&radius=2"
```

### 4.2 高级分析示例

#### Python脚本查询
```python
import requests

def analyze_knowledge_graph(api_url="http://127.0.0.1:8000"):
    # 获取统计信息
    stats_response = requests.get(f"{api_url}/api/v1/kg/stats")
    stats = stats_response.json()['data']
    
    print(f"图谱规模: {stats['basic']['num_nodes']}个节点, {stats['basic']['num_edges']}条边")
    print(f"关系类型: {len(stats['basic']['relationships'])}种")
    
    # 分析重要实体
    top_entities = stats['top_entities'][:10]
    print("\n重要实体排名:")
    for i, entity in enumerate(top_entities, 1):
        print(f"{i}. {entity['entity']} (度数: {entity['degree']}, 类型: {entity['type']})")
    
    return stats

# 使用示例
analyze_knowledge_graph()
```

#### 关系网络分析
```python
def explore_entity_network(entity_name, api_url="http://127.0.0.1:8000"):
    # 获取实体的邻居网络
    neighbors_response = requests.get(
        f"{api_url}/api/v1/kg/neighbors",
        params={"entity": entity_name}
    )
    
    data = neighbors_response.json()['data']
    nodes = data['nodes']
    edges = data['edges']
    
    print(f"\n{entity_name} 的关系网络:")
    print(f"直接连接的实体: {len(nodes)}个")
    print(f"关系数量: {len(edges)}条")
    
    # 分析连接的实体类型
    entity_types = {}
    for node in nodes:
        node_type = node['type']
        entity_types[node_type] = entity_types.get(node_type, 0) + 1
    
    print(f"连接的实体类型分布: {entity_types}")
    
    return data

# 使用示例
explore_entity_network("Python")
explore_entity_network("机器学习")
```

---

## 🎨 前端界面使用

### 启动Streamlit界面

```bash
# 启动前端界面
uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py

# 访问地址: http://localhost:8501
```

### 界面功能

1. **知识图谱可视化**: 交互式图谱展示
2. **实体搜索**: 快速查找特定概念
3. **关系探索**: 点击节点查看关联
4. **文本上传**: 直接上传文档构建图谱
5. **统计分析**: 实时图谱分析面板

---

## 📈 性能优化建议

### 文本预处理

```python
def preprocess_text(text):
    """文本预处理优化知识抽取效果"""
    import re
    
    # 清理文本
    text = re.sub(r'\s+', ' ', text)  # 合并多个空格
    text = text.strip()
    
    # 分段处理（避免过长文本）
    paragraphs = text.split('\n\n')
    processed_paragraphs = []
    
    for paragraph in paragraphs:
        if len(paragraph) > 500:
            # 按句子分割长段落
            sentences = paragraph.split('。')
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < 500:
                    current_chunk += sentence + "。"
                else:
                    if current_chunk:
                        processed_paragraphs.append(current_chunk.strip())
                    current_chunk = sentence + "。"
            
            if current_chunk:
                processed_paragraphs.append(current_chunk.strip())
        else:
            processed_paragraphs.append(paragraph)
    
    return processed_paragraphs

# 使用示例
def build_kg_optimized(text, source):
    chunks = preprocess_text(text)
    
    for i, chunk in enumerate(chunks):
        requests.post("http://127.0.0.1:8000/api/v1/kg/build", 
            json={
                "text": chunk,
                "source": f"{source}_chunk_{i}"
            }
        )
```

### 批量处理策略

```python
import asyncio
import aiohttp

async def batch_build_knowledge_graph(text_files, batch_size=3):
    """异步批量处理文本文件"""
    
    async def process_file(session, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        async with session.post(
            "http://127.0.0.1:8000/api/v1/kg/build",
            json={"text": text, "source": os.path.basename(filepath)}
        ) as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        # 分批处理文件
        for i in range(0, len(text_files), batch_size):
            batch = text_files[i:i+batch_size]
            tasks = [process_file(session, filepath) for filepath in batch]
            results = await asyncio.gather(*tasks)
            
            print(f"批次 {i//batch_size + 1} 完成:")
            for result in results:
                print(f"  - {result}")
            
            # 批次间的延迟
            await asyncio.sleep(1)

# 使用示例
text_files = [
    "data/sample_texts/ai_ml_article.txt",
    "data/sample_texts/science_discovery.txt", 
    "data/sample_texts/education_theory.txt"
]
asyncio.run(batch_build_knowledge_graph(text_files))
```

---

## 🛠 故障排除

### 常见问题

#### 1. API服务无法启动
```bash
# 检查端口占用
lsof -i :8000

# 查看环境变量
cat environments/test.env | grep -E "(REDIS|OPENAI|ZHIPU)"

# 重新加载环境
export $(cat environments/test.env | grep -v '^#' | xargs)
```

#### 2. 知识抽取质量不佳
- **检查文本质量**: 确保文本结构清晰，避免过多口语化
- **调整文本长度**: 单次处理建议1000-3000字符
- **优化API配置**: 检查LLM API密钥和模型设置

#### 3. 中文实体搜索问题
```python
import urllib.parse

# URL编码中文查询
query = urllib.parse.quote("人工智能")
url = f"http://127.0.0.1:8000/api/v1/kg/search?query={query}&limit=5"
```

#### 4. 图谱规模过大
- **分批构建**: 使用文件分块处理
- **设置限制**: 在API调用中添加限制参数
- **定期清理**: 删除不重要的节点和边

---

## 📊 效果评估

### 评估指标

```python
def evaluate_knowledge_extraction(api_url="http://127.0.0.1:8000"):
    """评估知识抽取效果"""
    
    stats_response = requests.get(f"{api_url}/api/v1/kg/stats")
    stats = stats_response.json()['data']
    
    metrics = {
        "节点总数": stats['basic']['num_nodes'],
        "边总数": stats['basic']['num_edges'],
        "平均度数": stats['basic']['avg_degree'],
        "连通组件数": stats['structure']['connectivity']['num_components'],
        "最大组件大小": stats['structure']['connectivity']['largest_component_size'],
        "关系类型数": len(stats['basic']['relationships']),
        "覆盖度": 1 - (stats['structure']['connectivity']['num_components'] / stats['basic']['num_nodes'])
    }
    
    print("知识抽取效果评估:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value}")
    
    return metrics
```

### 质量检查清单

- [ ] **完整性**: 重要概念是否被抽取？
- [ ] **准确性**: 关系是否正确？
- [ ] **连通性**: 相关概念是否建立了联系？
- [ ] **多样性**: 关系类型是否丰富？
- [ ] **一致性**: 同一概念是否重复出现？

---

## 🎯 最佳实践

### 1. 文本准备
- 选择结构化的文档（学术论文、技术文档、百科条目）
- 确保文本逻辑清晰，概念定义明确
- 避免过多的指代词和模糊表达

### 2. 增量构建
```python
def incremental_build(new_texts, existing_graph_stats):
    """增量式知识图谱构建"""
    
    # 检查现有图谱规模
    if existing_graph_stats['basic']['num_nodes'] > 1000:
        print("图谱规模较大，建议分批处理")
    
    # 逐步添加新内容
    for i, text in enumerate(new_texts):
        print(f"处理第{i+1}个文档...")
        # 调用构建API
        # 检查构建结果
        # 验证新增内容质量
```

### 3. 定期维护
```python
def maintain_knowledge_graph():
    """定期维护知识图谱"""
    
    # 1. 清理孤立节点
    # 2. 合并相似实体  
    # 3. 验证关系准确性
    # 4. 更新重要性排名
    # 5. 备份图谱数据
    pass
```

### 4. 多领域集成
- 为不同领域的文本使用不同的source标识
- 分析跨领域的关联关系
- 建立领域间的桥接概念

---

## 🔗 相关资源

- **API文档**: http://localhost:8000/docs
- **系统架构**: README.md
- **配置指南**: docs/configuration_guide.md
- **测试报告**: docs/knowledge_systems_test_report.md

---

## 🎉 总结

通过本指南的演示，我们成功地：

1. **处理真实数据**: 从3个不同领域的文章中抽取了99个三元组
2. **构建大型图谱**: 创建了包含141个节点、119条边的知识网络
3. **验证系统能力**: 展示了丰富的查询和分析功能
4. **提供实用工具**: 创建了完整的使用流程和最佳实践

**系统现已具备处理真实知识抽取任务的能力，可以应用于：**
- 学术文献分析
- 技术文档知识化
- 教育内容结构化
- 领域知识图谱构建
- 智能问答系统支撑

开始你的知识图谱构建之旅吧！🚀
