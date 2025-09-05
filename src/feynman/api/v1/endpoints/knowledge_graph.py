"""
知识图谱API端点
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from feynman.core.graph.service import get_knowledge_graph_service
from feynman.core.graph.schema import KnowledgeGraphBuildRequest, KnowledgeGraphQuery

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/build")
async def build_knowledge_graph(
    request: KnowledgeGraphBuildRequest,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    构建知识图谱
    
    支持从文本内容或文件路径构建知识图谱
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        if request.text:
            result = await kg_service.build_from_text(request.text)
        elif request.file_path:
            result = await kg_service.build_from_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400, 
                detail="请提供文本内容或文件路径"
            )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": result["message"],
                    "data": {
                        "triples_added": result.get("added_triples", 0),
                        "total_nodes": result.get("graph_stats", {}).get("num_nodes", 0),
                        "total_edges": result.get("graph_stats", {}).get("num_edges", 0)
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "message": result.get("message", "构建失败"),
                    "error": result.get("error")
                }
            )
            
    except Exception as e:
        logger.error(f"知识图谱构建API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/graph")
async def get_knowledge_graph(
    topic: Optional[str] = Query(None, description="主题过滤"),
    limit: Optional[int] = Query(1000, description="返回节点数限制")
) -> JSONResponse:
    """
    获取知识图谱数据
    
    支持按主题过滤和数量限制
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        query = KnowledgeGraphQuery(
            query_type="full",
            topic_filter=topic,
            limit=limit
        )
        
        graph_data = kg_service.query_graph(query)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "获取知识图谱成功",
                "data": graph_data.to_dict()
            }
        )
        
    except Exception as e:
        logger.error(f"获取知识图谱API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/subgraph")
async def get_subgraph(
    center: str = Query(..., description="中心节点"),
    radius: int = Query(1, description="查询半径")
) -> JSONResponse:
    """
    获取子图
    
    以指定节点为中心，获取指定半径内的子图
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        query = KnowledgeGraphQuery(
            query_type="subgraph",
            center_node=center,
            radius=radius
        )
        
        subgraph_data = kg_service.query_graph(query)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"获取以'{center}'为中心的子图成功",
                "data": subgraph_data.to_dict()
            }
        )
        
    except Exception as e:
        logger.error(f"获取子图API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/neighbors")
async def get_entity_neighbors(
    entity: str = Query(..., description="实体名称")
) -> JSONResponse:
    """
    获取实体的邻居节点
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        query = KnowledgeGraphQuery(
            query_type="neighbors",
            center_node=entity
        )
        
        neighbors_data = kg_service.query_graph(query)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"获取实体'{entity}'的邻居成功",
                "data": neighbors_data.to_dict()
            }
        )
        
    except Exception as e:
        logger.error(f"获取邻居API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/stats")
async def get_graph_stats() -> JSONResponse:
    """
    获取知识图谱统计信息
    """
    try:
        kg_service = get_knowledge_graph_service()
        stats = kg_service.get_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "获取统计信息成功",
                "data": stats
            }
        )
        
    except Exception as e:
        logger.error(f"获取统计信息API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/search")
async def search_entities(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(10, description="返回结果数限制")
) -> JSONResponse:
    """
    搜索实体
    """
    try:
        kg_service = get_knowledge_graph_service()
        results = kg_service.search_entities(query, limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"搜索实体'{query}'成功",
                "data": {
                    "entities": results,
                    "count": len(results)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"搜索实体API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/entity/{entity_id}/context")
async def get_entity_context(
    entity_id: str,
    radius: int = Query(1, description="上下文半径")
) -> JSONResponse:
    """
    获取实体的上下文信息
    """
    try:
        kg_service = get_knowledge_graph_service()
        context = kg_service.get_entity_context(entity_id, radius)
        
        if "error" in context:
            raise HTTPException(status_code=400, detail=context["error"])
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"获取实体'{entity_id}'的上下文成功",
                "data": context
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体上下文API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.delete("/clear")
async def clear_knowledge_graph() -> JSONResponse:
    """
    清空知识图谱
    """
    try:
        kg_service = get_knowledge_graph_service()
        kg_service.storage.clear()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "知识图谱已清空"
            }
        )
        
    except Exception as e:
        logger.error(f"清空知识图谱API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/build/conversation")
async def build_from_conversation(
    conversation_data: Dict[str, Any]
) -> JSONResponse:
    """
    从对话历史构建知识图谱
    """
    try:
        kg_service = get_knowledge_graph_service()
        
        conversation_history = conversation_data.get("conversation_history", [])
        if not conversation_history:
            raise HTTPException(
                status_code=400,
                detail="请提供对话历史数据"
            )
        
        result = await kg_service.build_from_conversation(conversation_history)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": result["message"],
                    "data": {
                        "triples_added": result.get("added_triples", 0),
                        "total_nodes": result.get("graph_stats", {}).get("num_nodes", 0),
                        "total_edges": result.get("graph_stats", {}).get("num_edges", 0)
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "message": result.get("message", "构建失败"),
                    "error": result.get("error")
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从对话构建知识图谱API错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

