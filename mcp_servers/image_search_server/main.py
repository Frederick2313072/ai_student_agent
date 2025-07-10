import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from serpapi import GoogleSearch

# --- 初始化与配置 ---
# 从 .env 文件加载环境变量 (主要是SERPAPI_API_KEY)
# 注意：路径是相对于项目根目录
load_dotenv() 

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# --- 数据模型定义 ---

class ImageResult(BaseModel):
    """单个图片搜索结果的模型"""
    url: str = Field(..., description="图片的直接链接", alias="original")
    title: str = Field(..., description="图片标题或描述")
    source: str = Field(..., description="图片来源网站", alias="source_name")

class SearchResponse(BaseModel):
    """API响应体模型"""
    query: str
    results: List[ImageResult]


# --- FastAPI应用初始化 ---

app = FastAPI(
    title="Image Search MCP Server",
    description="一个独立的MCP服务器，使用SerpApi提供真实的图像搜索功能。",
    version="1.1"
)

if not SERPAPI_API_KEY:
    print("警告：SERPAPI_API_KEY 未在.env文件中设置。图像搜索服务将无法工作。")


# --- 真实的外部API调用 ---

def _real_external_image_search(query: str, api_key: str) -> List[dict]:
    """
    使用SerpApi调用Google Images进行真实的图像搜索。
    """
    if not api_key:
        raise ValueError("SerpApi API key 未提供。")

    print(f"--- (MCP Server) 调用真实SerpApi进行搜索: {query} ---")
    
    params = {
        "engine": "google_images",
        "q": query,
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    
    # 从返回结果中提取图片列表
    image_results = results.get("images_results", [])

    # 为了与模型兼容，我们重命名一些键
    for item in image_results:
        item['source_name'] = item.get('source', 'N/A')

    return image_results


# --- API端点定义 ---

@app.get("/search", response_model=SearchResponse)
async def search_images(q: str = Query(..., min_length=1, description="要搜索的图像关键词")):
    """
    接收关键词并返回图像搜索结果。
    """
    if not SERPAPI_API_KEY:
        raise HTTPException(status_code=503, detail="图像搜索服务未配置API Key，暂时无法使用。")

    print(f"--- (MCP Server) 收到搜索请求: {q} ---")
    try:
        # 1. 调用外部服务
        raw_results = _real_external_image_search(q, SERPAPI_API_KEY)
        
        # 2. 使用Pydantic模型进行数据清洗和验证
        # Pydantic会自动处理在ImageResult中定义的'alias'
        clean_results = [ImageResult.model_validate(item) for item in raw_results[:5]] # 最多返回5条
        
        print(f"--- (MCP Server) 返回 {len(clean_results)} 条结果 ---")
        return SearchResponse(query=q, results=clean_results)

    except ValueError as ve:
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"--- (MCP Server) 发生错误: {e} ---")
        raise HTTPException(status_code=500, detail=f"图像搜索服务遇到内部错误: {e}")


@app.get("/")
def read_root():
    return {"message": "图像搜索MCP服务器已就绪。请使用/search端点。"}

# --- 用于本地开发的启动命令 ---
# uvicorn mcp_servers.image_search_server.main:app --reload --port 8001 