"""
知识图谱构建器

负责从三元组构建图、去重、合并等高层操作。
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
import difflib

from .schema import KnowledgeTriple, GraphData
from .storage import GraphStorageBackend, create_storage_backend

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, storage_backend: GraphStorageBackend):
        """初始化构建器"""
        self.storage = storage_backend
        self.similarity_threshold = 0.8  # 实体相似度阈值
    
    def build_from_triples(self, triples: List[KnowledgeTriple]) -> Dict[str, Any]:
        """从三元组列表构建知识图谱"""
        try:
            logger.info(f"开始构建知识图谱，输入 {len(triples)} 个三元组")
            
            # 1. 实体合并和规范化
            normalized_triples = self._normalize_and_merge_entities(triples)
            logger.info(f"实体合并后剩余 {len(normalized_triples)} 个三元组")
            
            # 2. 关系去重和合并
            merged_triples = self._merge_duplicate_relations(normalized_triples)
            logger.info(f"关系去重后剩余 {len(merged_triples)} 个三元组")
            
            # 3. 批量添加到存储
            added_count = self.storage.add_triples(merged_triples)
            
            # 4. 获取构建结果统计
            stats = self.storage.get_stats()
            
            result = {
                "success": True,
                "input_triples": len(triples),
                "processed_triples": len(normalized_triples),
                "merged_triples": len(merged_triples),
                "added_triples": added_count,
                "graph_stats": stats
            }
            
            logger.info(f"知识图谱构建完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_triples": len(triples)
            }
    
    def _normalize_and_merge_entities(self, triples: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """实体规范化和合并"""
        # 收集所有实体
        all_entities = set()
        for triple in triples:
            all_entities.add(triple.subject)
            all_entities.add(triple.object)
        
        # 构建实体映射（相似实体合并）
        entity_mapping = self._build_entity_mapping(list(all_entities))
        
        # 应用实体映射
        normalized_triples = []
        for triple in triples:
            normalized_subject = entity_mapping.get(triple.subject, triple.subject)
            normalized_object = entity_mapping.get(triple.object, triple.object)
            
            # 避免自环
            if normalized_subject != normalized_object:
                normalized_triple = KnowledgeTriple(
                    subject=normalized_subject,
                    predicate=triple.predicate,
                    object=normalized_object,
                    confidence=triple.confidence,
                    source=triple.source,
                    timestamp=triple.timestamp
                )
                normalized_triples.append(normalized_triple)
        
        return normalized_triples
    
    def _build_entity_mapping(self, entities: List[str]) -> Dict[str, str]:
        """构建实体映射表，将相似实体合并"""
        entity_mapping = {}
        processed = set()
        
        for entity in entities:
            if entity in processed:
                continue
            
            # 寻找相似实体
            similar_entities = [entity]
            for other_entity in entities:
                if other_entity != entity and other_entity not in processed:
                    similarity = self._calculate_similarity(entity, other_entity)
                    if similarity >= self.similarity_threshold:
                        similar_entities.append(other_entity)
            
            # 选择最代表性的实体作为主实体（通常是最短的）
            canonical_entity = min(similar_entities, key=len)
            
            # 建立映射
            for similar_entity in similar_entities:
                entity_mapping[similar_entity] = canonical_entity
                processed.add(similar_entity)
        
        return entity_mapping
    
    def _calculate_similarity(self, entity1: str, entity2: str) -> float:
        """计算两个实体的相似度"""
        # 简单的字符串相似度计算
        return difflib.SequenceMatcher(None, entity1.lower(), entity2.lower()).ratio()
    
    def _merge_duplicate_relations(self, triples: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """合并重复的关系"""
        # 按 (subject, predicate, object) 分组
        relation_groups = defaultdict(list)
        
        for triple in triples:
            key = (triple.subject, triple.predicate, triple.object)
            relation_groups[key].append(triple)
        
        # 合并每组中的三元组
        merged_triples = []
        for key, group_triples in relation_groups.items():
            if len(group_triples) == 1:
                merged_triples.append(group_triples[0])
            else:
                # 合并多个相同的三元组
                merged_triple = self._merge_triple_group(group_triples)
                merged_triples.append(merged_triple)
        
        return merged_triples
    
    def _merge_triple_group(self, triples: List[KnowledgeTriple]) -> KnowledgeTriple:
        """合并同一组三元组"""
        # 使用最高置信度
        max_confidence = max(triple.confidence for triple in triples)
        
        # 合并来源信息
        sources = [triple.source for triple in triples if triple.source]
        merged_source = "; ".join(set(sources)) if sources else None
        
        # 使用最早的时间戳
        earliest_timestamp = min(triple.timestamp for triple in triples)
        
        return KnowledgeTriple(
            subject=triples[0].subject,
            predicate=triples[0].predicate,
            object=triples[0].object,
            confidence=max_confidence,
            source=merged_source,
            timestamp=earliest_timestamp
        )
    
    def merge_graphs(self, other_builder: 'KnowledgeGraphBuilder') -> Dict[str, Any]:
        """合并另一个图构建器的数据"""
        try:
            # 获取另一个图的数据
            other_graph_data = other_builder.storage.get_graph()
            
            # 重建三元组并合并
            other_triples = self._graph_data_to_triples(other_graph_data)
            
            return self.build_from_triples(other_triples)
            
        except Exception as e:
            logger.error(f"合并图失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _graph_data_to_triples(self, graph_data: GraphData) -> List[KnowledgeTriple]:
        """将图数据转换回三元组列表"""
        triples = []
        
        # 从边重建三元组
        for edge in graph_data.edges:
            # 查找对应的节点标签
            source_node = next((node for node in graph_data.nodes if node.id == edge.source), None)
            target_node = next((node for node in graph_data.nodes if node.id == edge.target), None)
            
            if source_node and target_node:
                triple = KnowledgeTriple(
                    subject=source_node.label,
                    predicate=edge.relationship,
                    object=target_node.label,
                    confidence=edge.weight,
                    source=edge.properties.get("source")
                )
                triples.append(triple)
        
        return triples
    
    def analyze_graph_structure(self) -> Dict[str, Any]:
        """分析图结构特征"""
        try:
            graph_data = self.storage.get_graph()
            
            # 节点度分析
            node_degrees = [node.degree for node in graph_data.nodes]
            
            # 关系类型分析
            relationship_counts = Counter(edge.relationship for edge in graph_data.edges)
            
            # 连通性分析（对于NetworkX后端）
            connectivity_info = {}
            if hasattr(self.storage, 'graph'):
                import networkx as nx
                if isinstance(self.storage.graph, nx.Graph):
                    # 计算连通分量
                    components = list(nx.weakly_connected_components(self.storage.graph))
                    connectivity_info = {
                        "num_components": len(components),
                        "largest_component_size": max(len(comp) for comp in components) if components else 0,
                        "average_component_size": sum(len(comp) for comp in components) / len(components) if components else 0
                    }
            
            return {
                "node_analysis": {
                    "total_nodes": len(graph_data.nodes),
                    "avg_degree": sum(node_degrees) / len(node_degrees) if node_degrees else 0,
                    "max_degree": max(node_degrees) if node_degrees else 0,
                    "min_degree": min(node_degrees) if node_degrees else 0
                },
                "edge_analysis": {
                    "total_edges": len(graph_data.edges),
                    "relationship_types": dict(relationship_counts),
                    "most_common_relation": relationship_counts.most_common(1)[0] if relationship_counts else None
                },
                "connectivity": connectivity_info,
                "metadata": graph_data.metadata
            }
            
        except Exception as e:
            logger.error(f"分析图结构失败: {e}")
            return {"error": str(e)}
    
    def get_entity_importance_ranking(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """获取实体重要性排名"""
        try:
            graph_data = self.storage.get_graph()
            
            # 按度数排序
            ranked_nodes = sorted(graph_data.nodes, key=lambda n: n.degree, reverse=True)
            
            return [
                {
                    "entity": node.label,
                    "id": node.id,
                    "degree": node.degree,
                    "type": node.node_type
                }
                for node in ranked_nodes[:top_k]
            ]
            
        except Exception as e:
            logger.error(f"获取实体重要性排名失败: {e}")
            return []

