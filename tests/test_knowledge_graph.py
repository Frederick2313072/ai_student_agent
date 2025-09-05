"""
知识图谱功能测试
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch

from src.feynman.core.graph.schema import KnowledgeTriple, GraphData
from src.feynman.core.graph.extractor import KnowledgeExtractor
from src.feynman.core.graph.storage import NetworkXStorage
from src.feynman.core.graph.builder import KnowledgeGraphBuilder
from src.feynman.core.graph.service import KnowledgeGraphService


class TestKnowledgeTriple:
    """测试知识三元组"""
    
    def test_triple_creation(self):
        """测试三元组创建"""
        triple = KnowledgeTriple(
            subject="Python",
            predicate="是",
            object="编程语言",
            confidence=0.9
        )
        
        assert triple.subject == "Python"
        assert triple.predicate == "是"
        assert triple.object == "编程语言"
        assert triple.confidence == 0.9
        assert len(triple.get_id()) == 12  # MD5哈希前12位
    
    def test_triple_deduplication(self):
        """测试三元组去重"""
        triple1 = KnowledgeTriple(subject="Python", predicate="是", object="编程语言")
        triple2 = KnowledgeTriple(subject="Python", predicate="是", object="编程语言")
        
        assert triple1.get_id() == triple2.get_id()


class TestNetworkXStorage:
    """测试NetworkX存储"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.storage = NetworkXStorage(self.temp_file.name)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_add_triple(self):
        """测试添加三元组"""
        triple = KnowledgeTriple(
            subject="Python",
            predicate="支持",
            object="面向对象编程"
        )
        
        result = self.storage.add_triple(triple)
        assert result is True
        
        # 验证图中有相应的节点和边
        assert self.storage.graph.has_node("python")
        assert self.storage.graph.has_node("面向对象编程")
        assert self.storage.graph.has_edge("python", "面向对象编程")
    
    def test_get_graph(self):
        """测试获取图数据"""
        # 添加测试数据
        triples = [
            KnowledgeTriple(subject="Python", predicate="是", object="编程语言"),
            KnowledgeTriple(subject="Python", predicate="支持", object="面向对象编程"),
            KnowledgeTriple(subject="编程语言", predicate="用于", object="软件开发")
        ]
        
        for triple in triples:
            self.storage.add_triple(triple)
        
        graph_data = self.storage.get_graph()
        assert len(graph_data.nodes) == 3  # Python, 编程语言, 面向对象编程, 软件开发
        assert len(graph_data.edges) == 3
    
    def test_get_subgraph(self):
        """测试获取子图"""
        # 添加测试数据
        triples = [
            KnowledgeTriple(subject="Python", predicate="是", object="编程语言"),
            KnowledgeTriple(subject="Python", predicate="支持", object="面向对象编程"),
            KnowledgeTriple(subject="Java", predicate="是", object="编程语言")
        ]
        
        for triple in triples:
            self.storage.add_triple(triple)
        
        subgraph = self.storage.get_subgraph("Python", radius=1)
        assert len(subgraph.nodes) >= 2  # 至少包含Python和相关节点


class TestKnowledgeExtractor:
    """测试知识抽取器"""
    
    def setup_method(self):
        """测试前准备"""
        self.extractor = KnowledgeExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_triples_mock(self):
        """测试三元组抽取（使用Mock）"""
        test_text = "Python是一种编程语言，它支持面向对象编程。"
        
        # Mock LLM响应
        mock_response = Mock()
        mock_response.content = '''
        {
            "triples": [
                {
                    "subject": "Python",
                    "predicate": "是",
                    "object": "编程语言",
                    "confidence": 0.9
                },
                {
                    "subject": "Python",
                    "predicate": "支持",
                    "object": "面向对象编程",
                    "confidence": 0.8
                }
            ]
        }
        '''
        
        with patch.object(self.extractor, 'llm') as mock_llm:
            mock_llm.ainvoke.return_value = mock_response
            mock_llm.__bool__ = lambda x: True  # 模拟LLM可用
            
            triples = await self.extractor.extract_triples_llm(test_text)
            
            assert len(triples) == 2
            assert triples[0].subject == "Python"
            assert triples[0].predicate == "是"
            assert triples[0].object == "编程语言"


class TestKnowledgeGraphBuilder:
    """测试知识图谱构建器"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.storage = NetworkXStorage(self.temp_file.name)
        self.builder = KnowledgeGraphBuilder(self.storage)
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_build_from_triples(self):
        """测试从三元组构建图"""
        triples = [
            KnowledgeTriple(subject="Python", predicate="是", object="编程语言"),
            KnowledgeTriple(subject="python", predicate="是", object="编程语言"),  # 测试去重
            KnowledgeTriple(subject="Python", predicate="支持", object="面向对象编程")
        ]
        
        result = self.builder.build_from_triples(triples)
        
        assert result["success"] is True
        assert result["added_triples"] == 2  # 去重后应该只有2个
        assert result["graph_stats"]["num_nodes"] >= 2


class TestKnowledgeGraphService:
    """测试知识图谱服务"""
    
    def setup_method(self):
        """测试前准备"""
        with patch('src.feynman.core.graph.service.KnowledgeGraphService._init_storage') as mock_storage:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_file.close()
            mock_storage.return_value = NetworkXStorage(temp_file.name)
            self.service = KnowledgeGraphService()
            self.temp_file_path = temp_file.name
    
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)
    
    @pytest.mark.asyncio
    async def test_build_from_text_mock(self):
        """测试从文本构建（Mock）"""
        test_text = "Python是一种编程语言"
        
        # Mock抽取器
        mock_triples = [
            KnowledgeTriple(subject="Python", predicate="是", object="编程语言")
        ]
        
        with patch.object(self.service.extractor, 'extract_triples', return_value=mock_triples):
            result = await self.service.build_from_text(test_text)
            
            assert result["success"] is True
            assert "添加了" in result["message"]


# 集成测试
class TestKnowledgeGraphIntegration:
    """知识图谱集成测试"""
    
    def test_sample_knowledge_processing(self):
        """测试样本知识处理"""
        sample_text = """
        Python是一种高级编程语言。
        Python支持面向对象编程和函数式编程。
        Python被广泛用于数据科学和人工智能领域。
        """
        
        # 这里可以加载实际的样本数据进行测试
        # 但由于依赖外部服务，暂时跳过
        pass


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])

