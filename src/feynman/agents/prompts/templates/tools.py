"""
工具相关提示词模板

包含各种工具的错误消息、帮助信息和输出格式模板。
"""

# =============================================================================
# 工具错误消息模板
# =============================================================================

tool_error_messages = {
    # 知识库相关错误
    "rag_db_not_found": "RAG知识库目录 '{directory}' 不存在。请先运行ingest.py来创建它。",
    "memory_db_unavailable": "长期记忆数据库不可用，跳过记忆存储",
    "embeddings_unavailable": "嵌入模型不可用，知识检索功能将受限",
    
    # API密钥相关错误  
    "api_key_missing": "{service}不可用：请在环境变量中配置 {key_name}",
    "openai_key_missing": "OPENAI_API_KEY未设置，知识检索功能将受限", 
    "tavily_key_missing": "未配置 TAVILY_API_KEY，网络搜索工具不可用。请在 .env 设置 TAVILY_API_KEY 后重启服务。",
    "baidu_translate_key_missing": "翻译服务不可用：请在环境变量中配置 BAIDU_TRANSLATE_API_KEY 和 BAIDU_TRANSLATE_SECRET_KEY",
    "youtube_key_missing": "视频搜索不可用：请在环境变量中配置 YOUTUBE_API_KEY",
    "news_key_missing": "新闻搜索不可用：请在环境变量中配置 NEWS_API_KEY", 
    "judge0_key_missing": "代码执行不可用：请在环境变量中配置 JUDGE0_API_KEY",
    
    # 文件操作错误
    "file_operation_invalid": "错误: 无效的操作。请使用 'read' 或 'write'。",
    "file_operation_failed": "文件操作失败: {error}",
    
    # API调用错误
    "api_request_failed": "{service} API请求失败: {error}",
    "api_quota_exceeded": "{service} API配额已用完，请稍后再试",
    "api_timeout": "{service} API请求超时，请稍后重试",
    
    # 工具执行错误
    "tool_execution_failed": "工具 {tool_name} 执行失败: {error}",
    "tool_not_available": "工具 {tool_name} 当前不可用",
    "invalid_parameters": "工具参数无效: {details}"
}

# =============================================================================
# 工具帮助消息模板  
# =============================================================================

tool_help_messages = {
    # 核心工具帮助
    "knowledge_retriever": {
        "description": "查询外部RAG知识库。当对用户解释中的某个事实感到不确定，或希望从更权威的角度进行对比时调用。",
        "usage": "knowledge_retriever(query='查询内容')",
        "examples": ["knowledge_retriever('机器学习基本概念')", "knowledge_retriever('Python面向对象编程')"]
    },
    
    "memory_retriever": {
        "description": "查询内部长期记忆。当需要回忆之前的对话内容、避免重复提问、或进行关联思考时调用。",
        "usage": "memory_retriever(query='查询内容')",
        "examples": ["memory_retriever('之前讨论的数据结构')", "memory_retriever('用户对算法的理解')"]
    },
    
    "web_search": {
        "description": "搜索最新的网络信息。用于获取实时信息、验证事实、查找最新发展。",
        "usage": "web_search(query='搜索关键词')",
        "examples": ["web_search('Python 3.12新特性')", "web_search('机器学习最新进展2024')"]
    },
    
    # 学术工具帮助
    "search_academic_papers": {
        "description": "搜索arXiv学术论文。用于查找权威的学术资源和最新研究。",
        "usage": "search_academic_papers(query='研究主题', max_results=5)",
        "examples": ["search_academic_papers('transformer architecture')", "search_academic_papers('强化学习')"]
    },
    
    "search_wikipedia": {
        "description": "搜索Wikipedia获取基础概念解释。适合查找概念定义和背景知识。",
        "usage": "search_wikipedia(query='概念名称')",
        "examples": ["search_wikipedia('深度学习')", "search_wikipedia('量子计算')"]
    },
    
    # 计算工具帮助
    "calculate_math": {
        "description": "进行数学计算和公式验证。支持复杂数学表达式和科学计算。",
        "usage": "calculate_math(expression='数学表达式')",
        "examples": ["calculate_math('sqrt(2) + log(10)')", "calculate_math('integral of x^2 from 0 to 1')"]
    },
    
    "execute_code": {
        "description": "执行代码验证程序逻辑。支持多种编程语言的代码运行。", 
        "usage": "execute_code(code='代码内容', language='语言名')",
        "examples": ["execute_code('print(\"Hello World\")', 'python')", "execute_code('console.log(\"test\")', 'javascript')"]
    },
    
    # 可视化工具帮助
    "create_mindmap": {
        "description": "创建思维导图。用于可视化知识结构和概念关系。",
        "usage": "create_mindmap(topic='主题', content='内容描述', style='样式')",
        "examples": ["create_mindmap('机器学习', '监督学习、无监督学习、强化学习', 'mermaid')"]
    },
    
    "create_flowchart": {
        "description": "创建流程图。用于展示流程、算法或决策逻辑。",
        "usage": "create_flowchart(title='标题', description='流程描述', style='样式')",
        "examples": ["create_flowchart('算法流程', '输入数据->处理->输出结果', 'mermaid')"]
    }
}

# =============================================================================
# 思维导图输出模板
# =============================================================================

mindmap_output_templates = {
    "mermaid_success": """
✅ 思维导图创建成功！

**Mermaid代码:**
```mermaid
{mermaid_code}
```

**在线预览**: {online_url}
**图片链接**: {image_url}

你可以：
1. 复制Mermaid代码到支持的编辑器中
2. 点击在线链接直接查看和编辑
3. 使用图片链接在文档中引用
""",

    "plantuml_success": """
✅ 思维导图创建成功！

**PlantUML代码:**
```plantuml
{plantuml_code}
```

**在线预览**: {online_url}
**PNG图片**: {plantuml_png}

你可以：
1. 复制PlantUML代码到本地工具中
2. 访问在线链接查看图表
3. 下载PNG图片使用
""",

    "quickchart_success": """
✅ 思维导图创建成功！

**图片链接**: {chart_url}

你可以：
1. 访问图片链接查看思维导图
2. 右键保存图片到本地
3. 在文档中引用此图片链接
""",

    "creation_failed": "思维导图创建失败: {error}，请稍后重试或尝试其他样式。"
}

# =============================================================================
# 流程图输出模板
# =============================================================================

flowchart_output_templates = {
    "mermaid_success": """
✅ 流程图创建成功！

**Mermaid代码:**
```mermaid
{mermaid_code}
```

**在线预览**: {online_url}
**图片链接**: {image_url}

你可以：
1. 复制代码到支持Mermaid的编辑器
2. 点击链接在线查看和编辑
3. 使用图片链接嵌入文档
""",

    "plantuml_success": """
✅ 流程图创建成功！

**PlantUML代码:**
```plantuml
{plantuml_code}
```

**在线预览**: {online_url}
**PNG图片**: {plantuml_png}

你可以：
1. 复制代码到PlantUML编辑器
2. 访问在线链接查看
3. 下载PNG图片使用
""",

    "creation_failed": "流程图创建失败: {error}，请稍后重试或尝试其他样式。"
}

# =============================================================================
# API响应格式化模板
# =============================================================================

api_response_templates = {
    "search_result": """
🔍 搜索结果：

**查询**: {query}
**来源**: {source}
**结果数**: {count}

{results}
""",

    "calculation_result": """
🧮 计算结果：

**表达式**: {expression}
**结果**: {result}
**解释**: {explanation}
""",

    "translation_result": """
🌐 翻译结果：

**原文** ({source_lang}): {source_text}
**译文** ({target_lang}): {translated_text}
**置信度**: {confidence}
""",

    "code_execution_result": """
💻 代码执行结果：

**语言**: {language}
**状态**: {status}
**输出**: 
```
{output}
```
{error_info}
""",

    "academic_paper_result": """
📚 学术论文搜索结果：

**搜索词**: {query}
**找到**: {count} 篇相关论文

{papers}
""",

    "news_result": """
📰 新闻搜索结果：

**关键词**: {query}
**时间范围**: {time_range}
**结果数**: {count}

{articles}
"""
}

# =============================================================================
# 工具状态消息模板
# =============================================================================

tool_status_messages = {
    "initializing": "正在初始化 {tool_name}...",
    "processing": "正在处理 {operation}...",
    "success": "✅ {tool_name} 执行成功",
    "partial_success": "⚠️ {tool_name} 部分成功: {details}",
    "failed": "❌ {tool_name} 执行失败: {error}",
    "retry": "🔄 正在重试 {tool_name}... (第 {attempt} 次)",
    "fallback": "🔀 切换到备用方案: {fallback_method}",
    "timeout": "⏰ {tool_name} 执行超时",
    "rate_limited": "🚦 {tool_name} 达到速率限制，请稍后重试"
}

# =============================================================================
# 工具配置提示模板
# =============================================================================

tool_configuration_tips = {
    "setup_required": """
⚙️ 工具配置需要

要使用 {tool_name}，请配置以下环境变量：
{required_vars}

配置步骤：
1. 在 .env 文件中添加相应的API密钥
2. 重启应用以加载新配置
3. 运行测试验证配置是否正确

获取API密钥: {api_docs_url}
""",

    "optional_config": """
💡 可选配置

{tool_name} 支持以下可选配置：
{optional_vars}

这些配置可以改善工具性能但不是必需的。
""",

    "troubleshooting": """
🔧 故障排除

如果 {tool_name} 工作不正常，请检查：
1. API密钥是否正确配置
2. 网络连接是否正常
3. API服务是否可用
4. 是否超过了API配额限制

详细帮助: {help_url}
"""
}

# =============================================================================
# 提示词元数据
# =============================================================================

tool_prompt_metadata = {
    "version": "3.2.0",
    "last_updated": "2024-08-20",
    "description": "工具相关提示词和消息模板",
    "categories": [
        "错误消息",
        "帮助信息", 
        "输出格式化",
        "状态消息",
        "配置提示"
    ]
}
