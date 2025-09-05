"""
知识图谱存储后端

支持NetworkX本地存储和可选的Neo4j图数据库。
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import networkx as nx
from datetime import datetime

from .schema import KnowledgeTriple, GraphNode, GraphEdge, GraphData

logger = logging.getLogger(__name__)


class GraphStorageBackend(ABC):
    """图存储后端抽象基类"""
    
    @abstractmethod
    def add_triple(self, triple: KnowledgeTriple) -> bool:
        """添加三元组"""
        pass
    
    @abstractmethod
    def add_triples(self, triples: List[KnowledgeTriple]) -> int:
        """批量添加三元组"""
        pass
    
    @abstractmethod
    def get_graph(self, topic_filter: Optional[str] = None, limit: Optional[int] = None) -> GraphData:
        """获取图数据"""
        pass
    
    @abstractmethod
    def get_subgraph(self, center_node: str, radius: int = 1) -> GraphData:
        """获取子图"""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str) -> List[str]:
        """获取邻居节点"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取图统计信息"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空图数据"""
        pass


class NetworkXStorage(GraphStorageBackend):
    """基于NetworkX的本地存储"""
    
    def __init__(self, storage_path: str = "data/knowledge_graph.json"):
        """初始化NetworkX存储"""
        self.storage_path = storage_path
        self.graph = nx.MultiDiGraph()  # 支持多重有向图
        self.triples_data = {}  # 存储三元组的详细信息
        self._ensure_storage_dir()
        self.load_graph()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
    
    def add_triple(self, triple: KnowledgeTriple) -> bool:
        """添加单个三元组"""
        try:
            triple_id = triple.get_id()
            
            # 避免重复添加
            if triple_id in self.triples_data:
                return False
            
            # 添加节点
            subject_id = self._normalize_entity(triple.subject)
            object_id = self._normalize_entity(triple.object)
            
            if not self.graph.has_node(subject_id):
                self.graph.add_node(subject_id, label=triple.subject, type="entity")
            if not self.graph.has_node(object_id):
                self.graph.add_node(object_id, label=triple.object, type="entity")
            
            # 添加边
            self.graph.add_edge(
                subject_id, 
                object_id,
                key=triple_id,
                relationship=triple.predicate,
                weight=triple.confidence,
                source=triple.source,
                timestamp=triple.timestamp.isoformat()
            )
            
            # 存储三元组详细信息
            self.triples_data[triple_id] = triple.to_dict()
            
            return True
            
        except Exception as e:
            logger.error(f"添加三元组失败: {e}")
            return False
    
    def add_triples(self, triples: List[KnowledgeTriple]) -> int:
        """批量添加三元组"""
        added_count = 0
        for triple in triples:
            if self.add_triple(triple):
                added_count += 1
        
        # 保存到文件
        self.save_graph()
        return added_count
    
    def get_graph(self, topic_filter: Optional[str] = None, limit: Optional[int] = None) -> GraphData:
        """获取完整图数据"""
        try:
            nodes = []
            edges = []
            
            # 获取所有节点
            for node_id in self.graph.nodes():
                node_data = self.graph.nodes[node_id]
                node = GraphNode(
                    id=node_id,
                    label=node_data.get("label", node_id),
                    node_type=node_data.get("type", "entity"),
                    degree=self.graph.degree(node_id),
                    properties=node_data
                )
                nodes.append(node)
            
            # 获取所有边
            for u, v, key, edge_data in self.graph.edges(keys=True, data=True):
                edge = GraphEdge(
                    id=key,
                    source=u,
                    target=v,
                    relationship=edge_data.get("relationship", "相关"),
                    weight=edge_data.get("weight", 1.0),
                    properties=edge_data
                )
                edges.append(edge)
            
            # 应用过滤和限制
            if topic_filter:
                nodes, edges = self._filter_by_topic(nodes, edges, topic_filter)
            
            if limit:
                nodes = nodes[:limit]
                # 只保留相关的边
                node_ids = {node.id for node in nodes}
                edges = [edge for edge in edges if edge.source in node_ids and edge.target in node_ids]
            
            return GraphData(
                nodes=nodes,
                edges=edges,
                metadata={
                    "total_nodes": len(self.graph.nodes()),
                    "total_edges": len(self.graph.edges()),
                    "filtered": bool(topic_filter or limit)
                }
            )
            
        except Exception as e:
            logger.error(f"获取图数据失败: {e}")
            return GraphData()
    
    def get_subgraph(self, center_node: str, radius: int = 1) -> GraphData:
        """获取以指定节点为中心的子图"""
        try:
            center_id = self._normalize_entity(center_node)
            
            if not self.graph.has_node(center_id):
                logger.warning(f"中心节点 {center_node} 不存在")
                return GraphData()
            
            # 获取指定半径内的所有节点
            subgraph_nodes = set([center_id])
            current_nodes = {center_id}
            
            for _ in range(radius):
                next_nodes = set()
                for node in current_nodes:
                    # 获取所有邻居（入边和出边）
                    neighbors = set(self.graph.neighbors(node)) | set(self.graph.predecessors(node))
                    next_nodes.update(neighbors)
                
                subgraph_nodes.update(next_nodes)
                current_nodes = next_nodes
            
            # 创建子图
            subgraph = self.graph.subgraph(subgraph_nodes)
            
            # 转换为GraphData格式
            nodes = []
            for node_id in subgraph.nodes():
                node_data = subgraph.nodes[node_id]
                node = GraphNode(
                    id=node_id,
                    label=node_data.get("label", node_id),
                    node_type=node_data.get("type", "entity"),
                    degree=subgraph.degree(node_id),
                    properties=node_data
                )
                nodes.append(node)
            
            edges = []
            for u, v, key, edge_data in subgraph.edges(keys=True, data=True):
                edge = GraphEdge(
                    id=key,
                    source=u,
                    target=v,
                    relationship=edge_data.get("relationship", "相关"),
                    weight=edge_data.get("weight", 1.0),
                    properties=edge_data
                )
                edges.append(edge)
            
            return GraphData(
                nodes=nodes,
                edges=edges,
                metadata={
                    "center_node": center_node,
                    "radius": radius,
                    "subgraph_size": len(nodes)
                }
            )
            
        except Exception as e:
            logger.error(f"获取子图失败: {e}")
            return GraphData()
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """获取邻居节点"""
        try:
            normalized_id = self._normalize_entity(node_id)
            if not self.graph.has_node(normalized_id):
                return []
            
            neighbors = list(self.graph.neighbors(normalized_id))
            predecessors = list(self.graph.predecessors(normalized_id))
            return list(set(neighbors + predecessors))
            
        except Exception as e:
            logger.error(f"获取邻居节点失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取图统计信息"""
        try:
            num_nodes = self.graph.number_of_nodes()
            num_edges = self.graph.number_of_edges()
            
            # 计算度分布
            degrees = [self.graph.degree(n) for n in self.graph.nodes()]
            avg_degree = sum(degrees) / len(degrees) if degrees else 0
            
            # 获取关系类型分布
            relationships = {}
            for _, _, edge_data in self.graph.edges(data=True):
                rel = edge_data.get("relationship", "unknown")
                relationships[rel] = relationships.get(rel, 0) + 1
            
            return {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "avg_degree": round(avg_degree, 2),
                "max_degree": max(degrees) if degrees else 0,
                "relationships": relationships,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear(self):
        """清空图数据"""
        self.graph.clear()
        self.triples_data.clear()
        self.save_graph()
    
    def save_graph(self):
        """保存图到文件"""
        try:
            graph_data = {
                "nodes": [],
                "edges": [],
                "triples": self.triples_data,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "num_nodes": self.graph.number_of_nodes(),
                    "num_edges": self.graph.number_of_edges()
                }
            }
            
            # 保存节点
            for node_id, node_data in self.graph.nodes(data=True):
                graph_data["nodes"].append({
                    "id": node_id,
                    **node_data
                })
            
            # 保存边
            for u, v, key, edge_data in self.graph.edges(keys=True, data=True):
                graph_data["edges"].append({
                    "source": u,
                    "target": v,
                    "key": key,
                    **edge_data
                })
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"图数据已保存到 {self.storage_path}")
            
        except Exception as e:
            logger.error(f"保存图数据失败: {e}")
    
    def load_graph(self):
        """从文件加载图"""
        try:
            if not os.path.exists(self.storage_path):
                logger.info("图数据文件不存在，初始化空图")
                return
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # 重建图
            self.graph.clear()
            self.triples_data.clear()
            
            # 加载节点
            for node_data in graph_data.get("nodes", []):
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)
            
            # 加载边
            for edge_data in graph_data.get("edges", []):
                u = edge_data.pop("source")
                v = edge_data.pop("target")
                key = edge_data.pop("key")
                self.graph.add_edge(u, v, key=key, **edge_data)
            
            # 加载三元组数据
            self.triples_data = graph_data.get("triples", {})
            
            logger.info(f"成功加载图数据：{self.graph.number_of_nodes()} 个节点，{self.graph.number_of_edges()} 条边")
            
        except Exception as e:
            logger.error(f"加载图数据失败: {e}")
            self.graph = nx.MultiDiGraph()
            self.triples_data = {}
    
    def _normalize_entity(self, entity: str) -> str:
        """规范化实体名称作为节点ID"""
        return entity.strip().lower().replace(" ", "_")
    
    def _filter_by_topic(self, nodes: List[GraphNode], edges: List[GraphEdge], topic: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """按主题过滤节点和边"""
        topic_lower = topic.lower()
        
        # 过滤包含主题关键词的节点
        filtered_nodes = []
        for node in nodes:
            if (topic_lower in node.label.lower() or 
                topic_lower in node.id.lower() or
                any(topic_lower in str(v).lower() for v in node.properties.values())):
                filtered_nodes.append(node)
        
        # 保留相关的边
        node_ids = {node.id for node in filtered_nodes}
        filtered_edges = [edge for edge in edges if edge.source in node_ids and edge.target in node_ids]
        
        return filtered_nodes, filtered_edges


class Neo4jStorage(GraphStorageBackend):
    """基于Neo4j的图数据库存储（可选）"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """初始化Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.database = database
            logger.info("Neo4j连接成功")
        except ImportError:
            logger.error("neo4j包未安装，请运行: pip install neo4j")
            raise
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            raise
    
    def add_triple(self, triple: KnowledgeTriple) -> bool:
        """添加三元组到Neo4j"""
        try:
            with self.driver.session(database=self.database) as session:
                query = """
                MERGE (s:Entity {name: $subject})
                MERGE (o:Entity {name: $object})
                MERGE (s)-[r:RELATION {
                    type: $predicate,
                    confidence: $confidence,
                    source: $source,
                    timestamp: $timestamp,
                    triple_id: $triple_id
                }]->(o)
                RETURN r
                """
                result = session.run(query, {
                    "subject": triple.subject,
                    "object": triple.object,
                    "predicate": triple.predicate,
                    "confidence": triple.confidence,
                    "source": triple.source,
                    "timestamp": triple.timestamp.isoformat(),
                    "triple_id": triple.get_id()
                })
                return len(list(result)) > 0
                
        except Exception as e:
            logger.error(f"Neo4j添加三元组失败: {e}")
            return False
    
    def add_triples(self, triples: List[KnowledgeTriple]) -> int:
        """批量添加三元组"""
        added_count = 0
        for triple in triples:
            if self.add_triple(triple):
                added_count += 1
        return added_count
    
    def get_graph(self, topic_filter: Optional[str] = None, limit: Optional[int] = None) -> GraphData:
        """从Neo4j获取图数据"""
        try:
            with self.driver.session(database=self.database) as session:
                # 构建查询
                if topic_filter:
                    query = """
                    MATCH (n:Entity)-[r:RELATION]->(m:Entity)
                    WHERE toLower(n.name) CONTAINS toLower($topic) 
                       OR toLower(m.name) CONTAINS toLower($topic)
                       OR toLower(r.type) CONTAINS toLower($topic)
                    RETURN n, r, m
                    LIMIT $limit
                    """
                    params = {"topic": topic_filter, "limit": limit or 1000}
                else:
                    query = """
                    MATCH (n:Entity)-[r:RELATION]->(m:Entity)
                    RETURN n, r, m
                    LIMIT $limit
                    """
                    params = {"limit": limit or 1000}
                
                result = session.run(query, params)
                
                nodes_dict = {}
                edges = []
                
                for record in result:
                    # 处理节点
                    n_node = record["n"]
                    m_node = record["m"]
                    relation = record["r"]
                    
                    # 添加源节点
                    n_id = self._normalize_entity(n_node["name"])
                    if n_id not in nodes_dict:
                        nodes_dict[n_id] = GraphNode(
                            id=n_id,
                            label=n_node["name"],
                            node_type="entity",
                            degree=0  # 后续计算
                        )
                    
                    # 添加目标节点
                    m_id = self._normalize_entity(m_node["name"])
                    if m_id not in nodes_dict:
                        nodes_dict[m_id] = GraphNode(
                            id=m_id,
                            label=m_node["name"],
                            node_type="entity",
                            degree=0  # 后续计算
                        )
                    
                    # 添加边
                    edge = GraphEdge(
                        id=relation.get("triple_id", f"{n_id}_{m_id}"),
                        source=n_id,
                        target=m_id,
                        relationship=relation["type"],
                        weight=relation.get("confidence", 1.0),
                        properties={
                            "source": relation.get("source"),
                            "timestamp": relation.get("timestamp")
                        }
                    )
                    edges.append(edge)
                
                # 计算节点度数
                for edge in edges:
                    if edge.source in nodes_dict:
                        nodes_dict[edge.source].degree += 1
                    if edge.target in nodes_dict:
                        nodes_dict[edge.target].degree += 1
                
                return GraphData(
                    nodes=list(nodes_dict.values()),
                    edges=edges,
                    metadata={
                        "backend": "neo4j",
                        "filtered": bool(topic_filter),
                        "total_returned": len(nodes_dict)
                    }
                )
                
        except Exception as e:
            logger.error(f"Neo4j获取图数据失败: {e}")
            return GraphData()
    
    def get_subgraph(self, center_node: str, radius: int = 1) -> GraphData:
        """获取Neo4j子图"""
        try:
            with self.driver.session(database=self.database) as session:
                # 构建变长路径查询
                query = f"""
                MATCH (center:Entity {{name: $center_name}})
                MATCH path = (center)-[*1..{radius}]-(neighbor:Entity)
                WITH nodes(path) as path_nodes, relationships(path) as path_rels
                UNWIND path_nodes as node
                UNWIND path_rels as rel
                RETURN DISTINCT 
                    startNode(rel) as source_node,
                    endNode(rel) as target_node,
                    rel
                """
                
                result = session.run(query, {"center_name": center_node})
                
                nodes_dict = {}
                edges = []
                
                for record in result:
                    source_node = record["source_node"]
                    target_node = record["target_node"]
                    relation = record["rel"]
                    
                    # 添加源节点
                    source_id = self._normalize_entity(source_node["name"])
                    if source_id not in nodes_dict:
                        nodes_dict[source_id] = GraphNode(
                            id=source_id,
                            label=source_node["name"],
                            node_type="entity",
                            degree=0
                        )
                    
                    # 添加目标节点
                    target_id = self._normalize_entity(target_node["name"])
                    if target_id not in nodes_dict:
                        nodes_dict[target_id] = GraphNode(
                            id=target_id,
                            label=target_node["name"],
                            node_type="entity",
                            degree=0
                        )
                    
                    # 添加边
                    edge = GraphEdge(
                        id=relation.get("triple_id", f"{source_id}_{target_id}"),
                        source=source_id,
                        target=target_id,
                        relationship=relation["type"],
                        weight=relation.get("confidence", 1.0),
                        properties={
                            "source": relation.get("source"),
                            "timestamp": relation.get("timestamp")
                        }
                    )
                    edges.append(edge)
                
                # 计算度数
                for edge in edges:
                    if edge.source in nodes_dict:
                        nodes_dict[edge.source].degree += 1
                    if edge.target in nodes_dict:
                        nodes_dict[edge.target].degree += 1
                
                return GraphData(
                    nodes=list(nodes_dict.values()),
                    edges=edges,
                    metadata={
                        "center_node": center_node,
                        "radius": radius,
                        "backend": "neo4j"
                    }
                )
                
        except Exception as e:
            logger.error(f"Neo4j获取子图失败: {e}")
            return GraphData()
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """获取Neo4j邻居节点"""
        try:
            with self.driver.session(database=self.database) as session:
                query = """
                MATCH (n:Entity {name: $node_name})-[r]-(neighbor:Entity)
                RETURN DISTINCT neighbor.name as neighbor_name
                """
                result = session.run(query, {"node_name": node_id})
                return [record["neighbor_name"] for record in result]
                
        except Exception as e:
            logger.error(f"Neo4j获取邻居节点失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Neo4j图统计"""
        try:
            with self.driver.session(database=self.database) as session:
                # 节点数
                nodes_result = session.run("MATCH (n:Entity) RETURN COUNT(n) as count")
                num_nodes = nodes_result.single()["count"]
                
                # 关系数
                edges_result = session.run("MATCH ()-[r:RELATION]-() RETURN COUNT(r) as count")
                num_edges = edges_result.single()["count"]
                
                return {
                    "num_nodes": num_nodes,
                    "num_edges": num_edges,
                    "backend": "neo4j",
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Neo4j获取统计失败: {e}")
            return {}
    
    def clear(self):
        """清空Neo4j数据"""
        try:
            with self.driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Neo4j数据已清空")
        except Exception as e:
            logger.error(f"Neo4j清空数据失败: {e}")
    
    def close(self):
        """关闭Neo4j连接"""
        if hasattr(self, 'driver'):
            self.driver.close()


def create_storage_backend(backend_type: str = "local", **kwargs) -> GraphStorageBackend:
    """创建存储后端工厂函数"""
    if backend_type == "local":
        storage_path = kwargs.get("storage_path", "data/knowledge_graph.json")
        return NetworkXStorage(storage_path)
    elif backend_type == "neo4j":
        return Neo4jStorage(
            uri=kwargs["uri"],
            username=kwargs["username"], 
            password=kwargs["password"],
            database=kwargs.get("database", "neo4j")
        )
    else:
        raise ValueError(f"不支持的存储后端类型: {backend_type}")
