
import os
import json
import requests
from typing import List, Dict
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 初始化 ---
# 修正路径计算，使其相对于项目根目录
ABS_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DB_DIR = os.path.join(ABS_PATH, "knowledge_base")
MEMORY_DB_DIR = os.path.join(ABS_PATH, "long_term_memory")
IMAGE_SEARCH_API_URL = "http://127.0.0.1:8001/search" # MCP服务器地址

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

rag_db = Chroma(persist_directory=RAG_DB_DIR, embedding_function=embeddings) if os.path.exists(RAG_DB_DIR) else None
memory_db = Chroma(persist_directory=MEMORY_DB_DIR, embedding_function=embeddings) if os.path.exists(MEMORY_DB_DIR) else None

# --- 工具定义 ---

@tool
def knowledge_retriever(query: str) -> List[Dict]:
    """
    查询外部RAG知识库。当对用户解释中的某个事实感到不确定，或希望从更权威的角度进行对比时调用。
    """
    print(f"--- 外部知识库查询: {query} ---")
    if rag_db is None:
        return [{"source": "error", "content": f"RAG知识库目录 '{RAG_DB_DIR}' 不存在。请先运行ingest.py来创建它。"}]
    
    results = rag_db.similarity_search(query, k=2)
    return [{"source": doc.metadata.get('source', 'unknown'), "content": doc.page_content} for doc in results]

@tool
def memory_retriever(query: str) -> List[Dict]:
    """
    查询内部长期记忆。当需要回忆之前的对话内容、避免重复提问、或进行关联思考时调用。
    """
    print(f"--- 内部记忆查询: {query} ---")
    if memory_db is None:
        return [{"source": "error", "content": f"长期记忆数据库 '{MEMORY_DB_DIR}' 不存在。"}]
    results = memory_db.similarity_search(query, k=2)
    return [{"source": "long_term_memory", "content": doc.page_content} for doc in results]

@tool
def file_operation(operation: str, file_name: str, content: str = None) -> str:
    """
    执行文件操作，支持 'read' 或 'write'。
    """
    print(f"--- 文件操作: {operation} on {file_name} ---")
    try:
        if operation == 'write':
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件 '{file_name}' 已成功写入。"
        elif operation == 'read':
            with open(file_name, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "错误: 无效的操作。请使用 'read' 或 'write'。"
    except Exception as e:
        return f"文件操作失败: {e}"

# 使用Tavily实现网络搜索和网页抓取
# include_raw_content=True 可以让它获取网页内容，从而同时实现搜索和抓取
web_search = TavilySearchResults(max_results=3, include_raw_content=True)
web_search.name = "web_search"
web_search.description = "执行网络搜索并抓取网页内容，以验证信息或获取最新知识。输入应该是详细的搜索查询。"

# 废弃旧的占位符函数
# @tool
# def web_search(query: str) -> str:
# ...
# @tool
# def web_scrape(url: str) -> str:
# ...

@tool
def image_search(query: str) -> str:
    """
    进行图像搜索。此工具会调用一个独立的MCP服务器来获取结果。
    """
    print(f"--- 图像搜索工具: 调用MCP服务器 (Query: {query}) ---")
    try:
        response = requests.get(IMAGE_SEARCH_API_URL, params={"q": query}, timeout=10)
        response.raise_for_status() # 如果请求失败 (非2xx状态码)，则抛出异常
        
        # 将返回的JSON结果转换为格式化的字符串，以便LLM阅读
        results = response.json().get('results', [])
        if not results:
            return f"没有找到关于“{query}”的图片。"
            
        formatted_results = "\n".join([
            f"- 图片标题: {res['title']}, 链接: {res['url']}, 来源: {res['source']}" 
            for res in results
        ])
        return f"找到关于“{query}”的图片如下:\n{formatted_results}"

    except requests.exceptions.RequestException as e:
        print(f"--- 调用图像搜索MCP服务器失败: {e} ---")
        return f"错误：无法连接到图像搜索服务。请确认服务是否在 {IMAGE_SEARCH_API_URL} 上运行。"
    except json.JSONDecodeError:
        return "错误：图像搜索服务返回了无效的响应格式。" 