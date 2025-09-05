
import os
import json
import requests
import hashlib
import time
from typing import List, Dict, Optional
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 导入统一提示词管理
from feynman.agents.prompts.prompt_manager import prompt_manager, get_tool_error, get_api_response
from langchain_community.tools.tavily_search import TavilySearchResults

# 导入知识图谱服务
from feynman.core.graph.service import get_knowledge_graph_service
from feynman.core.graph.schema import KnowledgeGraphQuery

# --- 初始化 ---
# 路径计算
ABS_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DB_DIR = os.path.join(ABS_PATH, "knowledge_base")
MEMORY_DB_DIR = os.path.join(ABS_PATH, "long_term_memory")


base_url = os.getenv("OPENAI_BASE_URL", "").strip()

# 条件初始化嵌入模型
try:
    if os.getenv("OPENAI_API_KEY"):
        if base_url:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small", base_url=base_url)
        else:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        EMBEDDINGS_AVAILABLE = True
    else:

        embeddings = None
        EMBEDDINGS_AVAILABLE = False
except Exception as e:

    embeddings = None
    EMBEDDINGS_AVAILABLE = False

rag_db = None
memory_db = None

if EMBEDDINGS_AVAILABLE and embeddings:
    rag_db = Chroma(persist_directory=RAG_DB_DIR, embedding_function=embeddings) if os.path.exists(RAG_DB_DIR) else None
    memory_db = Chroma(persist_directory=MEMORY_DB_DIR, embedding_function=embeddings) if os.path.exists(MEMORY_DB_DIR) else None
else:
    rag_db = None
    memory_db = None

# 工具定义

@tool
def knowledge_retriever(query: str) -> List[Dict]:
    """
    查询外部RAG知识库。当对用户解释中的某个事实感到不确定，或希望从更权威的角度进行对比时调用。
    """

    if rag_db is None:
        return [{"source": "error", "content": get_tool_error("rag_db_not_found", directory=RAG_DB_DIR)}]
    
    results = rag_db.similarity_search(query, k=2)
    return [{"source": doc.metadata.get('source', 'unknown'), "content": doc.page_content} for doc in results]

@tool
def memory_retriever(query: str) -> List[Dict]:
    """
    查询内部长期记忆。当需要回忆之前的对话内容、避免重复提问、或进行关联思考时调用。
    """

    if memory_db is None:
        return [{"source": "error", "content": f"长期记忆数据库 '{MEMORY_DB_DIR}' 不存在。"}]
    results = memory_db.similarity_search(query, k=2)
    return [{"source": "long_term_memory", "content": doc.page_content} for doc in results]

@tool
def file_operation(operation: str, file_name: str, content: str = None) -> str:
    """
    执行文件操作，支持 'read' 或 'write'。
    """

    try:
        if operation == 'write':
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件 '{file_name}' 已成功写入。"
        elif operation == 'read':
            with open(file_name, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return get_tool_error("file_operation_invalid")
    except Exception as e:
        return get_tool_error("file_operation_failed", error=str(e))

"""
根据是否配置 TAVILY_API_KEY 决定启用真实的 Tavily 搜索工具，
否则降级为提示性占位工具，避免应用在启动阶段抛出校验错误。
"""
tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
if tavily_api_key:
    # 使用Tavily实现网络搜索和网页抓取
    # include_raw_content=True 可以让它获取网页内容，从而同时实现搜索和抓取
    web_search = TavilySearchResults(max_results=3, include_raw_content=True)
    web_search.name = "web_search"
    web_search.description = "执行网络搜索并抓取网页内容，以验证信息或获取最新知识。输入应该是详细的搜索查询。"
else:
    @tool
    def web_search(query: str) -> str:
        """占位网络搜索工具。未设置 TAVILY_API_KEY 时返回提示信息。"""
        return get_tool_error("tavily_key_missing")





# --- API工具 ---

@tool
def translate_text(text: str, target_lang: str = "zh", source_lang: str = "auto") -> str:
    """
    翻译文本。支持多种语言之间的翻译，用于处理多语言学习内容。
    target_lang: 目标语言代码 (zh=中文, en=英文, ja=日语, ko=韩语等)
    source_lang: 源语言代码 (auto=自动检测)
    """

    
    baidu_api_key = os.getenv("BAIDU_TRANSLATE_API_KEY", "").strip()
    baidu_secret_key = os.getenv("BAIDU_TRANSLATE_SECRET_KEY", "").strip()
    
    if not baidu_api_key or not baidu_secret_key:
        return get_tool_error("baidu_translate_key_missing")
    
    try:
        # 百度翻译API
        appid = baidu_api_key
        secret_key = baidu_secret_key
        salt = str(int(time.time()))
        sign_str = appid + text + salt + secret_key
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        params = {
            'q': text,
            'from': source_lang,
            'to': target_lang,
            'appid': appid,
            'salt': salt,
            'sign': sign
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if 'trans_result' in result:
            translations = [item['dst'] for item in result['trans_result']]
            return "\n".join(translations)
        else:
            return f"翻译失败：{result.get('error_msg', '未知错误')}"
            
    except Exception as e:
        return f"翻译服务错误：{str(e)}"

@tool  
def calculate_math(expression: str) -> str:
    """
    执行数学计算和求解。支持基础数学运算、方程求解、函数计算等。
    用于验证数学概念和计算结果。
    """

    
    wolfram_api_key = os.getenv("WOLFRAM_API_KEY", "").strip()
    
    if wolfram_api_key:
        try:
            # 使用WolframAlpha API
            url = "http://api.wolframalpha.com/v2/query"
            params = {
                'appid': wolfram_api_key,
                'input': expression,
                'format': 'plaintext',
                'output': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            pods = result.get('queryresult', {}).get('pods', [])
            
            if pods:
                output = []
                for pod in pods[:3]:  # 只取前3个结果
                    title = pod.get('title', '')
                    if 'subpods' in pod:
                        for subpod in pod['subpods']:
                            text = subpod.get('plaintext', '')
                            if text:
                                output.append(f"{title}: {text}")
                
                return "\n".join(output) if output else "未找到计算结果"
            else:
                return "WolframAlpha无法解析该表达式"
                
        except Exception as e:
            # 降级到Python内置计算
            pass
    
    # 降级方案：使用Python的eval进行基础计算
    try:
        # 安全的数学表达式计算
        import math
        import re
        
        # 只允许数字、运算符和数学函数
        if re.match(r'^[0-9+\-*/().\s√πe\^sincostandlogpowsqrtabs,]+$', expression.replace('**', '^')):
            # 替换一些常见的数学符号
            safe_expr = expression.replace('√', 'sqrt').replace('π', 'pi').replace('^', '**')
            safe_expr = safe_expr.replace('e', str(math.e)).replace('pi', str(math.pi))
            
            # 构建安全的命名空间
            safe_dict = {
                "abs": abs, "round": round, "pow": pow,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "log10": math.log10,
                "exp": math.exp, "pi": math.pi, "e": math.e
            }
            
            result = eval(safe_expr, {"__builtins__": {}}, safe_dict)
            return f"计算结果: {result}"
        else:
            return "表达式包含不安全的字符，无法计算"
            
    except Exception as e:
        return f"计算错误：{str(e)}。建议配置 WOLFRAM_API_KEY 以获得更强大的计算能力。"

@tool
def search_academic_papers(query: str, max_results: int = 5) -> str:
    """
    搜索学术论文和研究资料。用于查找权威的学术资料来验证学习内容。
    """

    
    try:
        # 使用arXiv API搜索
        arxiv_url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f"all:{query}",
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = requests.get(arxiv_url, params=params, timeout=15)
        response.raise_for_status()
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
            link = entry.find('{http://www.w3.org/2005/Atom}link').get('href')
            published = entry.find('{http://www.w3.org/2005/Atom}published').text[:10]
            
            authors = []
            for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                name = author.find('{http://www.w3.org/2005/Atom}name').text
                authors.append(name)
            
            papers.append({
                'title': title,
                'authors': ', '.join(authors),
                'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                'link': link,
                'published': published
            })
        
        if papers:
            result = f"找到 {len(papers)} 篇相关论文：\n\n"
            for i, paper in enumerate(papers, 1):
                result += f"{i}. **{paper['title']}**\n"
                result += f"   作者: {paper['authors']}\n"
                result += f"   发表日期: {paper['published']}\n"
                result += f"   摘要: {paper['summary']}\n"
                result += f"   链接: {paper['link']}\n\n"
            return result
        else:
            return f"未找到关于 '{query}' 的学术论文"
            
    except Exception as e:
        return f"学术搜索错误：{str(e)}"



@tool
def search_wikipedia(query: str, lang: str = "zh") -> str:
    """
    搜索维基百科条目。用于获取概念的权威定义和基础知识。
    lang: 语言代码 (zh=中文, en=英文)
    """

    
    try:
        # 搜索条目
        search_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}"
        
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', '')
            extract = data.get('extract', '')
            page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
            
            if extract:
                return f"**{title}**\n\n{extract}\n\n详细信息: {page_url}"
            else:
                return f"找到条目 '{title}' 但无摘要信息"
        else:
            # 尝试搜索相关条目
            search_api_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3
            }
            
            response = requests.get(search_api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            if search_results:
                suggestions = []
                for result in search_results:
                    title = result['title']
                    snippet = result['snippet'].replace('<span class="searchmatch">', '').replace('</span>', '')
                    suggestions.append(f"- {title}: {snippet}")
                
                return f"未找到精确匹配，相关条目：\n" + "\n".join(suggestions)
            else:
                return f"未找到关于 '{query}' 的维基百科条目"
                
    except Exception as e:
        return f"维基百科搜索错误：{str(e)}"



@tool
def execute_code(code: str, language: str = "python") -> str:
    """
    执行代码并返回结果。用于验证编程概念和运行示例代码。
    支持的语言: python, javascript, java, cpp等
    """

    
    judge0_api_key = os.getenv("JUDGE0_API_KEY", "").strip()
    
    if not judge0_api_key:
        return get_tool_error("judge0_key_missing")
    
    # 语言ID映射 (Judge0 API)
    language_ids = {
        'python': 71,      # Python 3
        'javascript': 63,  # Node.js
        'java': 62,        # Java
        'cpp': 54,         # C++
        'c': 50,           # C
        'php': 68,         # PHP
        'ruby': 72,        # Ruby
        'go': 60,          # Go
        'rust': 73,        # Rust
        'swift': 83,       # Swift
    }
    
    language_id = language_ids.get(language.lower())
    if not language_id:
        return f"不支持的编程语言: {language}。支持的语言: {', '.join(language_ids.keys())}"
    
    try:
        # 提交代码执行
        submit_url = "https://judge0-ce.p.rapidapi.com/submissions"
        headers = {
            "X-RapidAPI-Key": judge0_api_key,
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        
        data = {
            "source_code": code,
            "language_id": language_id,
            "stdin": "",
            "expected_output": ""
        }
        
        response = requests.post(submit_url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        submission = response.json()
        token = submission['token']
        
        # 等待执行完成
        time.sleep(2)
        
        # 获取结果
        result_url = f"https://judge0-ce.p.rapidapi.com/submissions/{token}"
        result_response = requests.get(result_url, headers=headers, timeout=10)
        result_response.raise_for_status()
        
        result = result_response.json()
        
        output_parts = []
        
        if result.get('stdout'):
            output_parts.append(f"输出:\n{result['stdout']}")
        
        if result.get('stderr'):
            output_parts.append(f"错误:\n{result['stderr']}")
        
        if result.get('compile_output'):
            output_parts.append(f"编译信息:\n{result['compile_output']}")
        
        status = result.get('status', {}).get('description', '未知')
        output_parts.append(f"执行状态: {status}")
        
        return "\n\n".join(output_parts) if output_parts else "代码执行完成，无输出"
        
    except Exception as e:
        return f"代码执行错误：{str(e)}"

@tool
def create_mindmap(topic: str, content: str, style: str = "mermaid") -> str:
    """
    创建思维导图。支持多种格式和样式，用于可视化知识结构和概念关系。
    topic: 思维导图主题
    content: 思维导图内容描述或结构化数据
    style: 思维导图样式 (mermaid, plantuml, quickchart)
    """

    
    if style.lower() == "mermaid":
        return _create_mermaid_mindmap(topic, content)
    elif style.lower() == "plantuml":
        return _create_plantuml_mindmap(topic, content)
    elif style.lower() == "quickchart":
        return _create_quickchart_mindmap(topic, content)
    else:
        return f"不支持的思维导图样式: {style}。支持的样式: mermaid, plantuml, quickchart"

def _create_mermaid_mindmap(topic: str, content: str) -> str:
    """使用Mermaid.js生成思维导图"""
    try:
        # 将内容转换为Mermaid语法
        mermaid_code = _convert_to_mermaid_syntax(topic, content)
        
        # 使用Mermaid在线渲染服务
        import urllib.parse
        encoded_diagram = urllib.parse.quote(mermaid_code)
        
        # Mermaid Live Editor API
        mermaid_url = f"https://mermaid.live/edit#{encoded_diagram}"
        
        # 使用mermaid.ink服务生成图片
        image_url = f"https://mermaid.ink/img/{encoded_diagram}"
        
        return prompt_manager.get_template("tool", "mindmap_templates")["mermaid_success"].format(
            mermaid_code=mermaid_code,
            online_url=mermaid_url,
            image_url=image_url
        )
        
    except Exception as e:
        return f"Mermaid思维导图生成失败: {str(e)}"

def _create_plantuml_mindmap(topic: str, content: str) -> str:
    """使用PlantUML生成思维导图"""
    try:
        # 将内容转换为PlantUML语法
        plantuml_code = _convert_to_plantuml_syntax(topic, content)
        
        # 使用PlantUML在线服务
        import base64
        import zlib
        
        # PlantUML压缩编码
        compressed = zlib.compress(plantuml_code.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        # PlantUML在线渲染链接
        plantuml_url = f"http://www.plantuml.com/plantuml/uml/{encoded}"
        plantuml_png = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        return f"""思维导图已生成 - {topic}

PlantUML代码:
```plantuml
{plantuml_code}
```

在线查看: {plantuml_url}
PNG图片: {plantuml_png}

你可以：
1. 复制PlantUML代码到本地工具中
2. 访问在线链接查看图表
3. 下载PNG图片使用
"""
        
    except Exception as e:
        return f"PlantUML思维导图生成失败: {str(e)}"

def _create_quickchart_mindmap(topic: str, content: str) -> str:
    """使用QuickChart API生成思维导图"""
    try:
        quickchart_api_key = os.getenv("QUICKCHART_API_KEY", "").strip()
        
        # 将内容转换为图表配置
        chart_config = _convert_to_chart_config(topic, content)
        
        url = "https://quickchart.io/chart"
        
        if quickchart_api_key:
            # 使用API密钥获得更高级功能
            params = {
                'c': json.dumps(chart_config),
                'key': quickchart_api_key,
                'format': 'png',
                'width': 800,
                'height': 600
            }
        else:
            # 免费版本
            params = {
                'c': json.dumps(chart_config),
                'format': 'png',
                'width': 600,
                'height': 400
            }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        # 构建图片URL
        chart_url = response.url
        
        return f"""思维导图已生成 - {topic}

图表配置:
```json
{json.dumps(chart_config, indent=2, ensure_ascii=False)}
```

图片链接: {chart_url}

你可以：
1. 访问图片链接查看思维导图
2. 右键保存图片到本地
3. 在文档中引用此图片链接
"""
        
    except Exception as e:
        return f"QuickChart思维导图生成失败: {str(e)}"

def _convert_to_mermaid_syntax(topic: str, content: str) -> str:
    """将内容转换为Mermaid思维导图语法"""
    # 简单的转换逻辑，可以根据需要扩展
    lines = content.strip().split('\n')
    mermaid_lines = ["mindmap", f"  root)({topic})"]
    
    for line in lines:
        line = line.strip()
        if line:
            # 检测层级（基于缩进或标记）
            if line.startswith('- ') or line.startswith('* '):
                clean_line = line[2:].strip()
                mermaid_lines.append(f"    {clean_line}")
            elif line.startswith('  - ') or line.startswith('  * '):
                clean_line = line[4:].strip()
                mermaid_lines.append(f"      {clean_line}")
            else:
                mermaid_lines.append(f"    {line}")
    
    return '\n'.join(mermaid_lines)

def _convert_to_plantuml_syntax(topic: str, content: str) -> str:
    """将内容转换为PlantUML思维导图语法"""
    lines = content.strip().split('\n')
    plantuml_lines = [
        "@startmindmap",
        f"* {topic}"
    ]
    
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('- ') or line.startswith('* '):
                clean_line = line[2:].strip()
                plantuml_lines.append(f"** {clean_line}")
            elif line.startswith('  - ') or line.startswith('  * '):
                clean_line = line[4:].strip()
                plantuml_lines.append(f"*** {clean_line}")
            else:
                plantuml_lines.append(f"** {line}")
    
    plantuml_lines.append("@endmindmap")
    return '\n'.join(plantuml_lines)

def _convert_to_chart_config(topic: str, content: str) -> dict:
    """将内容转换为QuickChart图表配置"""
    # 创建一个简单的网络图配置
    lines = content.strip().split('\n')
    
    nodes = [{"id": "root", "label": topic, "color": "#ff6b6b"}]
    edges = []
    
    node_id = 1
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('- ') or line.startswith('* '):
                clean_line = line[2:].strip()
                nodes.append({"id": f"node_{node_id}", "label": clean_line, "color": "#4ecdc4"})
                edges.append({"from": "root", "to": f"node_{node_id}"})
                node_id += 1
    
    return {
        "type": "network",
        "data": {
            "datasets": [{
                "data": nodes,
                "edges": edges
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": f"思维导图: {topic}"
            },
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD"
                }
            }
        }
    }

@tool
def create_flowchart(title: str, steps: str, style: str = "mermaid") -> str:
    """
    创建流程图。用于展示流程、算法或步骤序列。
    title: 流程图标题
    steps: 流程步骤描述
    style: 流程图样式 (mermaid, plantuml)
    """

    
    if style.lower() == "mermaid":
        return _create_mermaid_flowchart(title, steps)
    elif style.lower() == "plantuml":
        return _create_plantuml_flowchart(title, steps)
    else:
        return f"不支持的流程图样式: {style}。支持的样式: mermaid, plantuml"

def _create_mermaid_flowchart(title: str, steps: str) -> str:
    """使用Mermaid生成流程图"""
    try:
        # 将步骤转换为Mermaid流程图语法
        mermaid_code = _convert_to_mermaid_flowchart(title, steps)
        
        # 编码并生成链接
        import urllib.parse
        encoded_diagram = urllib.parse.quote(mermaid_code)
        
        mermaid_url = f"https://mermaid.live/edit#{encoded_diagram}"
        image_url = f"https://mermaid.ink/img/{encoded_diagram}"
        
        return f"""流程图已生成 - {title}

Mermaid代码:
```mermaid
{mermaid_code}
```

在线查看: {mermaid_url}
图片链接: {image_url}
"""
        
    except Exception as e:
        return f"Mermaid流程图生成失败: {str(e)}"

def _create_plantuml_flowchart(title: str, steps: str) -> str:
    """使用PlantUML生成流程图"""
    try:
        # 将步骤转换为PlantUML语法
        plantuml_code = _convert_to_plantuml_flowchart(title, steps)
        
        # 编码并生成链接
        import base64
        import zlib
        
        compressed = zlib.compress(plantuml_code.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        plantuml_url = f"http://www.plantuml.com/plantuml/uml/{encoded}"
        plantuml_png = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        return f"""流程图已生成 - {title}

PlantUML代码:
```plantuml
{plantuml_code}
```

在线查看: {plantuml_url}
PNG图片: {plantuml_png}
"""
        
    except Exception as e:
        return f"PlantUML流程图生成失败: {str(e)}"

def _convert_to_mermaid_flowchart(title: str, steps: str) -> str:
    """将步骤转换为Mermaid流程图语法"""
    lines = steps.strip().split('\n')
    mermaid_lines = ["flowchart TD"]
    
    step_id = 1
    prev_id = None
    
    for line in lines:
        line = line.strip()
        if line:
            current_id = f"A{step_id}"
            clean_line = line.replace('- ', '').replace('* ', '').strip()
            
            # 检测条件语句
            if '?' in clean_line or '是否' in clean_line:
                mermaid_lines.append(f"    {current_id}{{{clean_line}}}")
            else:
                mermaid_lines.append(f"    {current_id}[{clean_line}]")
            
            if prev_id:
                mermaid_lines.append(f"    {prev_id} --> {current_id}")
            
            prev_id = current_id
            step_id += 1
    
    return '\n'.join(mermaid_lines)

def _convert_to_plantuml_flowchart(title: str, steps: str) -> str:
    """将步骤转换为PlantUML流程图语法"""
    lines = steps.strip().split('\n')
    plantuml_lines = [
        "@startuml",
        f"title {title}",
        "start"
    ]
    
    for line in lines:
        line = line.strip()
        if line:
            clean_line = line.replace('- ', '').replace('* ', '').strip()
            
            if '?' in clean_line or '是否' in clean_line:
                plantuml_lines.append(f"if ({clean_line}) then (是)")
                plantuml_lines.append("else (否)")
                plantuml_lines.append("endif")
            else:
                plantuml_lines.append(f":{clean_line};")
    
    plantuml_lines.append("stop")
    plantuml_lines.append("@enduml")
    
    return '\n'.join(plantuml_lines)


# --- 知识图谱工具 ---

@tool
def graph_query(query: str, query_type: str = "search", center_node: str = None, radius: int = 1) -> str:
    """
    查询知识图谱
    
    参数:
    - query: 查询内容或搜索关键词
    - query_type: 查询类型 (search, subgraph, neighbors, stats)
    - center_node: 中心节点（subgraph和neighbors查询时需要）
    - radius: 查询半径（subgraph查询时使用）
    
    返回知识图谱中的相关信息，帮助Agent了解实体间的关系。
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        if query_type == "search":
            results = kg_service.search_entities(query, limit=10)
            if results:
                entities_info = []
                for entity in results:
                    entities_info.append(f"- {entity['label']} (度数: {entity['degree']}, 类型: {entity['type']})")
                return f"找到以下相关实体:\n" + "\n".join(entities_info)
            else:
                return f"未找到与'{query}'相关的实体"
        
        elif query_type == "subgraph":
            if not center_node:
                return "子图查询需要指定center_node参数"
            
            kg_query = KnowledgeGraphQuery(
                query_type="subgraph",
                center_node=center_node,
                radius=radius
            )
            subgraph = kg_service.query_graph(kg_query)
            
            if subgraph.nodes:
                nodes_info = [f"- {node.label}" for node in subgraph.nodes]
                relations_info = [f"- {edge.source} {edge.relationship} {edge.target}" for edge in subgraph.edges]
                
                result = f"以'{center_node}'为中心的子图:\n"
                result += f"节点 ({len(subgraph.nodes)}):\n" + "\n".join(nodes_info[:10])
                if len(nodes_info) > 10:
                    result += f"\n... 还有 {len(nodes_info) - 10} 个节点"
                
                result += f"\n\n关系 ({len(subgraph.edges)}):\n" + "\n".join(relations_info[:10])
                if len(relations_info) > 10:
                    result += f"\n... 还有 {len(relations_info) - 10} 个关系"
                
                return result
            else:
                return f"未找到以'{center_node}'为中心的子图"
        
        elif query_type == "neighbors":
            if not center_node:
                return "邻居查询需要指定center_node参数"
            
            neighbors = kg_service.storage.get_neighbors(center_node)
            if neighbors:
                return f"'{center_node}'的邻居节点:\n" + "\n".join(f"- {neighbor}" for neighbor in neighbors[:10])
            else:
                return f"'{center_node}'没有邻居节点"
        
        elif query_type == "stats":
            stats = kg_service.get_stats()
            basic_stats = stats.get("basic", {})
            top_entities = stats.get("top_entities", [])
            
            result = "知识图谱统计信息:\n"
            result += f"- 节点数: {basic_stats.get('num_nodes', 0)}\n"
            result += f"- 边数: {basic_stats.get('num_edges', 0)}\n"
            result += f"- 平均度数: {basic_stats.get('avg_degree', 0)}\n"
            
            if top_entities:
                result += "\n重要实体排名:\n"
                for i, entity in enumerate(top_entities[:5], 1):
                    result += f"{i}. {entity['entity']} (度数: {entity['degree']})\n"
            
            return result
        
        else:
            return f"不支持的查询类型: {query_type}"
    
    except Exception as e:
        error_msg = f"知识图谱查询失败: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def graph_explain(entity: str, depth: int = 1) -> str:
    """
    解释实体的知识图谱上下文
    
    参数:
    - entity: 要解释的实体名称
    - depth: 解释深度（1=直接关系，2=二阶关系）
    
    返回实体在知识图谱中的详细上下文信息。
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        context = kg_service.get_entity_context(entity, radius=depth)
        
        if "error" in context:
            return f"获取实体'{entity}'的上下文失败: {context['error']}"
        
        result = f"实体'{entity}'的知识图谱上下文:\n\n"
        
        triples = context.get("related_triples", [])
        if triples:
            result += "相关关系:\n"
            for triple in triples[:10]:
                result += f"- {triple['subject']} {triple['predicate']} {triple['object']}"
                if triple.get("confidence"):
                    result += f" (置信度: {triple['confidence']:.2f})"
                result += "\n"
            
            if len(triples) > 10:
                result += f"... 还有 {len(triples) - 10} 个关系\n"
        
        neighbors_count = context.get("neighbors_count", 0)
        result += f"\n邻居节点数: {neighbors_count}"
        
        subgraph = context.get("subgraph", {})
        if subgraph:
            result += f"\n子图规模: {len(subgraph.get('nodes', []))} 个节点, {len(subgraph.get('edges', []))} 条边"
        
        return result
        
    except Exception as e:
        error_msg = f"解释实体上下文失败: {str(e)}"
        logger.error(error_msg)
        return error_msg