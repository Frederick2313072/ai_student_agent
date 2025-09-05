"""
知识图谱服务层

为API和Agent提供统一的知识图谱操作接口。
"""

import logging
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio

from .extractor import KnowledgeExtractor
from .builder import KnowledgeGraphBuilder
from .storage import create_storage_backend, GraphStorageBackend
from .schema import KnowledgeTriple, GraphData, KnowledgeGraphQuery, KnowledgeGraphBuildRequest

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        """初始化服务"""
        self.extractor = KnowledgeExtractor()
        self.storage = self._init_storage()
        self.builder = KnowledgeGraphBuilder(self.storage)
    
    def _init_storage(self) -> GraphStorageBackend:
        """初始化存储后端"""
        backend_type = os.getenv("KG_BACKEND", "local").lower()
        
        if backend_type == "neo4j":
            try:
                return create_storage_backend(
                    "neo4j",
                    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    username=os.getenv("NEO4J_USERNAME", "neo4j"),
                    password=os.getenv("NEO4J_PASSWORD", "password"),
                    database=os.getenv("NEO4J_DATABASE", "neo4j")
                )
            except Exception as e:
                logger.warning(f"Neo4j初始化失败，回退到本地存储: {e}")
                backend_type = "local"
        
        if backend_type == "local":
            storage_path = os.getenv("KG_STORAGE_PATH", "data/knowledge_graph.json")
            return create_storage_backend("local", storage_path=storage_path)
        
        raise ValueError(f"不支持的存储后端: {backend_type}")
    
    async def build_from_text(self, text: str, source: Optional[str] = None) -> Dict[str, Any]:
        """从文本构建知识图谱"""
        try:
            logger.info(f"从文本构建知识图谱，文本长度: {len(text)}")
            
            # 1. 抽取三元组
            triples = await self.extractor.extract_triples(text, source)
            
            if not triples:
                logger.warning("未抽取到任何三元组")
                return {
                    "success": False,
                    "message": "未从文本中抽取到知识三元组。可能原因：1) LLM API不可用或余额不足 2) 文本内容不适合抽取结构化知识 3) 网络连接问题。请检查API配置或稍后重试。",
                    "triples_count": 0,
                    "suggestion": "建议检查LLM API配置、网络连接，或尝试更结构化的文本内容"
                }
            
            # 2. 构建图
            build_result = self.builder.build_from_triples(triples)
            
            return {
                "success": True,
                "message": f"成功构建知识图谱，添加了 {build_result.get('added_triples', 0)} 个三元组",
                **build_result
            }
            
        except Exception as e:
            logger.error(f"从文本构建知识图谱失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "构建知识图谱时发生错误"
            }
    
    async def build_from_file(self, file_path: str) -> Dict[str, Any]:
        """从文件构建知识图谱"""
        try:
            logger.info(f"从文件构建知识图谱: {file_path}")
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件不存在: {file_path}"
                }
            
            # 1. 抽取三元组
            triples = await self.extractor.extract_from_file(file_path)
            
            if not triples:
                return {
                    "success": False,
                    "message": f"未从文件 {file_path} 中抽取到知识三元组"
                }
            
            # 2. 构建图
            build_result = self.builder.build_from_triples(triples)
            
            return {
                "success": True,
                "message": f"成功从文件构建知识图谱，添加了 {build_result.get('added_triples', 0)} 个三元组",
                "file_path": file_path,
                **build_result
            }
            
        except Exception as e:
            logger.error(f"从文件构建知识图谱失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"从文件 {file_path} 构建知识图谱时发生错误"
            }
    
    def query_graph(self, query: KnowledgeGraphQuery) -> GraphData:
        """查询知识图谱"""
        try:
            logger.info(f"查询知识图谱: {query.query_type}")
            
            if query.query_type == "full":
                return self.storage.get_graph(
                    topic_filter=query.topic_filter,
                    limit=query.limit
                )
            
            elif query.query_type == "subgraph":
                if not query.center_node:
                    raise ValueError("子图查询需要指定中心节点")
                return self.storage.get_subgraph(
                    query.center_node,
                    query.radius or 1
                )
            
            elif query.query_type == "neighbors":
                if not query.center_node:
                    raise ValueError("邻居查询需要指定中心节点")
                neighbors = self.storage.get_neighbors(query.center_node)
                
                # 构建邻居子图
                if neighbors:
                    all_nodes = [query.center_node] + neighbors
                    return self._build_subgraph_from_nodes(all_nodes)
                else:
                    return GraphData()
            
            else:
                raise ValueError(f"不支持的查询类型: {query.query_type}")
                
        except Exception as e:
            logger.error(f"查询知识图谱失败: {e}")
            return GraphData()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        try:
            basic_stats = self.storage.get_stats()
            structure_analysis = self.builder.analyze_graph_structure()
            importance_ranking = self.builder.get_entity_importance_ranking()
            
            return {
                "basic": basic_stats,
                "structure": structure_analysis,
                "top_entities": importance_ranking
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索实体"""
        try:
            graph_data = self.storage.get_graph()
            query_lower = query.lower()
            
            # 模糊匹配实体
            matching_entities = []
            for node in graph_data.nodes:
                if query_lower in node.label.lower():
                    matching_entities.append({
                        "id": node.id,
                        "label": node.label,
                        "type": node.node_type,
                        "degree": node.degree,
                        "score": self._calculate_match_score(query_lower, node.label.lower())
                    })
            
            # 按匹配分数排序
            matching_entities.sort(key=lambda x: x["score"], reverse=True)
            return matching_entities[:limit]
            
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return []
    
    def get_entity_context(self, entity_id: str, radius: int = 1) -> Dict[str, Any]:
        """获取实体的上下文信息"""
        try:
            # 获取子图
            subgraph = self.storage.get_subgraph(entity_id, radius)
            
            # 获取相关三元组
            related_triples = []
            for edge in subgraph.edges:
                if edge.source == entity_id or edge.target == entity_id:
                    # 从边信息重建三元组
                    source_node = next((n for n in subgraph.nodes if n.id == edge.source), None)
                    target_node = next((n for n in subgraph.nodes if n.id == edge.target), None)
                    
                    if source_node and target_node:
                        related_triples.append({
                            "subject": source_node.label,
                            "predicate": edge.relationship,
                            "object": target_node.label,
                            "confidence": edge.weight,
                            "source": edge.properties.get("source")
                        })
            
            return {
                "entity": entity_id,
                "subgraph": subgraph.to_dict(),
                "related_triples": related_triples,
                "neighbors_count": len([n for n in subgraph.nodes if n.id != entity_id])
            }
            
        except Exception as e:
            logger.error(f"获取实体上下文失败: {e}")
            return {"error": str(e)}
    
    def _calculate_match_score(self, query: str, text: str) -> float:
        """计算匹配分数"""
        if query == text:
            return 1.0
        elif query in text:
            return 0.8
        else:
            # 简单的字符串相似度
            import difflib
            return difflib.SequenceMatcher(None, query, text).ratio()
    
    def _build_subgraph_from_nodes(self, node_ids: List[str]) -> GraphData:
        """从节点列表构建子图"""
        full_graph = self.storage.get_graph()
        
        # 过滤节点
        filtered_nodes = [node for node in full_graph.nodes if node.id in node_ids]
        node_id_set = set(node_ids)
        
        # 过滤边
        filtered_edges = [
            edge for edge in full_graph.edges 
            if edge.source in node_id_set and edge.target in node_id_set
        ]
        
        return GraphData(
            nodes=filtered_nodes,
            edges=filtered_edges,
            metadata={"type": "subgraph", "node_count": len(filtered_nodes)}
        )
    
    async def build_from_conversation(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """从对话历史构建知识图谱"""
        try:
            # 合并对话内容
            text_content = []
            for msg in conversation_history:
                if msg.get("role") in ["user", "assistant"]:
                    content = msg.get("content", "")
                    if content.strip():
                        text_content.append(content)
            
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                return {
                    "success": False,
                    "message": "对话内容为空"
                }
            
            # 构建知识图谱
            return await self.build_from_text(full_text, source="conversation")
            
        except Exception as e:
            logger.error(f"从对话构建知识图谱失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "从对话构建知识图谱时发生错误"
            }
    
    def export_graph(self, format: str = "json") -> Optional[str]:
        """导出知识图谱"""
        try:
            if format == "json":
                graph_data = self.storage.get_graph()
                return graph_data.model_dump_json(indent=2)
            
            elif format == "gexf" and hasattr(self.storage, 'graph'):
                # NetworkX GEXF格式
                import tempfile
                import networkx as nx
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.gexf', delete=False) as f:
                    nx.write_gexf(self.storage.graph, f.name)
                    return f.name
            
            else:
                logger.error(f"不支持的导出格式: {format}")
                return None
                
        except Exception as e:
            logger.error(f"导出知识图谱失败: {e}")
            return None


# 全局服务实例
_kg_service = None

def get_knowledge_graph_service() -> KnowledgeGraphService:
    """获取知识图谱服务单例"""
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    return _kg_service

