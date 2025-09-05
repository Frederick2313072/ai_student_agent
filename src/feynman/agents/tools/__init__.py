"""
工具模块 - AI Agent的核心工具集合

本模块统一管理所有Agent可用的工具，包括：
- 知识检索工具（RAG、记忆）
- 网络搜索工具（Web、学术、维基）
- 多媒体工具（翻译、计算、代码执行）
- 可视化工具（思维导图、流程图）
- 知识图谱工具（图查询、实体解释）
- 文件操作工具

所有工具实现位于tools.py，本文件仅负责统一导入和暴露API。
"""

from .tools import (
    # 核心检索工具
    knowledge_retriever,
    memory_retriever,
    file_operation,
    
    # 搜索工具
    web_search,
    search_academic_papers,
    search_wikipedia,
    
    # 处理工具
    translate_text,
    calculate_math,
    execute_code,
    
    # 可视化工具
    create_mindmap,
    create_flowchart,
    
    # 知识图谱工具
    graph_query,
    graph_explain
)

# 导出工具列表，供agent.py使用
ALL_TOOLS = [
    knowledge_retriever,
    memory_retriever,
    file_operation,
    web_search,
    translate_text,
    calculate_math,
    search_academic_papers,
    search_wikipedia,
    execute_code,
    create_mindmap,
    create_flowchart,
    graph_query,
    graph_explain
]

__all__ = [
    "knowledge_retriever",
    "memory_retriever", 
    "file_operation",
    "web_search",
    "translate_text",
    "calculate_math",
    "search_academic_papers",
    "search_wikipedia",
    "execute_code",
    "create_mindmap",
    "create_flowchart",
    "graph_query",
    "graph_explain",
    "ALL_TOOLS"
]
