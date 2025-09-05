"""
知识图谱数据模型定义
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib


class KnowledgeTriple(BaseModel):
    """知识三元组：(主体, 关系, 客体)"""
    subject: str = Field(..., description="主体实体")
    predicate: str = Field(..., description="关系谓词")
    object: str = Field(..., description="客体实体")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度")
    source: Optional[str] = Field(default=None, description="来源文档或对话ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def get_id(self) -> str:
        """生成三元组的唯一ID"""
        content = f"{self.subject}|{self.predicate}|{self.object}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.get_id(),
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }


class GraphNode(BaseModel):
    """图节点"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    node_type: str = Field(default="entity", description="节点类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    degree: int = Field(default=0, description="节点度数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties,
            "degree": self.degree
        }


class GraphEdge(BaseModel):
    """图边"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relationship: str = Field(..., description="关系类型")
    weight: float = Field(default=1.0, description="边权重")
    properties: Dict[str, Any] = Field(default_factory=dict, description="边属性")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "weight": self.weight,
            "properties": self.properties
        }


class GraphData(BaseModel):
    """完整图数据结构"""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取图统计信息"""
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "node_types": list(set(node.node_type for node in self.nodes)),
            "relationship_types": list(set(edge.relationship for edge in self.edges))
        }


class KnowledgeGraphQuery(BaseModel):
    """知识图谱查询请求"""
    query_type: str = Field(..., description="查询类型: subgraph, neighbors, path, stats")
    center_node: Optional[str] = Field(default=None, description="中心节点")
    radius: Optional[int] = Field(default=1, description="查询半径")
    topic_filter: Optional[str] = Field(default=None, description="主题过滤")
    limit: Optional[int] = Field(default=100, description="结果限制")


class KnowledgeGraphBuildRequest(BaseModel):
    """知识图谱构建请求"""
    text: Optional[str] = Field(default=None, description="要处理的文本")
    file_path: Optional[str] = Field(default=None, description="要处理的文件路径")
    build_options: Dict[str, Any] = Field(default_factory=dict, description="构建选项")

