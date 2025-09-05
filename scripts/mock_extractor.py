"""
模拟知识抽取器

用于测试的模拟LLM抽取器，不依赖真实API密钥。
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.feynman.core.graph.schema import KnowledgeTriple

logger = logging.getLogger(__name__)


class MockKnowledgeExtractor:
    """模拟知识抽取器"""
    
    def __init__(self):
        """初始化模拟抽取器"""
        self.patterns = self._create_extraction_patterns()
    
    def _create_extraction_patterns(self):
        """创建抽取模式"""
        return [
            # 定义模式: X是Y
            (r'(\w+)是([^，。]+)', "是"),
            # 包含模式: X包含Y, X包括Y
            (r'(\w+)包含([^，。]+)', "包含"),
            (r'(\w+)包括([^，。]+)', "包含"),
            # 用于模式: X用于Y, X应用于Y
            (r'(\w+)用于([^，。]+)', "用于"),
            (r'(\w+)应用于([^，。]+)', "用于"),
            # 支持模式: X支持Y
            (r'(\w+)支持([^，。]+)', "支持"),
            # 基于模式: X基于Y
            (r'(\w+)基于([^，。]+)', "基于"),
            # 提供模式: X提供Y
            (r'(\w+)提供([^，。]+)', "提供"),
            # 使用模式: X使用Y
            (r'(\w+)使用([^，。]+)', "使用"),
            # 开发模式: X开发Y, X创建Y
            (r'(\w+)开发([^，。]+)', "开发"),
            (r'(\w+)创建([^，。]+)', "开发"),
            # 属于模式: X属于Y
            (r'(\w+)属于([^，。]+)', "属于"),
            # 连接模式: X连接Y, X关联Y
            (r'(\w+)连接([^，。]+)', "连接"),
            (r'(\w+)关联([^，。]+)', "相关"),
        ]
    
    async def extract_triples(self, text: str, source: Optional[str] = None) -> List[KnowledgeTriple]:
        """
        使用规则模式抽取知识三元组
        """
        triples = []
        
        # 预处理文本
        text = self._preprocess_text(text)
        
        # 应用抽取模式
        for pattern, predicate in self.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                subject = match.group(1).strip()
                object_entity = match.group(2).strip()
                
                # 清理和验证
                subject = self._clean_entity(subject)
                object_entity = self._clean_entity(object_entity)
                
                if self._is_valid_entity(subject) and self._is_valid_entity(object_entity):
                    triple = KnowledgeTriple(
                        subject=subject,
                        predicate=predicate,
                        object=object_entity,
                        confidence=0.75,  # 模拟置信度
                        source=source,
                        timestamp=datetime.now()
                    )
                    triples.append(triple)
        
        # 额外的实体-关系抽取
        additional_triples = self._extract_additional_relations(text, source)
        triples.extend(additional_triples)
        
        # 去重
        unique_triples = self._deduplicate_triples(triples)
        
        logger.info(f"模拟抽取器从文本抽取到 {len(unique_triples)} 个三元组")
        return unique_triples
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s，。：；！？]', '', text)
        return text.strip()
    
    def _clean_entity(self, entity: str) -> str:
        """清理实体名称"""
        # 移除常见的无意义词汇
        stop_words = {'一个', '一种', '这个', '那个', '某个', '多个', '很多', '许多', '所有', '各种'}
        
        words = entity.split()
        cleaned_words = [word for word in words if word not in stop_words]
        
        return ' '.join(cleaned_words).strip()
    
    def _is_valid_entity(self, entity: str) -> bool:
        """验证实体是否有效"""
        if not entity or len(entity) < 2:
            return False
        
        # 排除无意义的实体
        invalid_patterns = [
            r'^\d+$',  # 纯数字
            r'^[一二三四五六七八九十百千万]+$',  # 纯中文数字
            r'^[的了在和与及其或者]$',  # 常见连词
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, entity):
                return False
        
        return True
    
    def _extract_additional_relations(self, text: str, source: Optional[str] = None) -> List[KnowledgeTriple]:
        """抽取额外的关系"""
        additional_triples = []
        
        # 时间关系抽取: 在X年
        year_pattern = r'在?(\d{4})年[^，。]*?([^，。]{2,10})([发布|推出|创建|成立])'
        year_matches = re.finditer(year_pattern, text)
        
        for match in year_matches:
            year = match.group(1)
            entity = self._clean_entity(match.group(2))
            action = match.group(3)
            
            if self._is_valid_entity(entity):
                triple = KnowledgeTriple(
                    subject=entity,
                    predicate=f"{action}于",
                    object=f"{year}年",
                    confidence=0.8,
                    source=source,
                    timestamp=datetime.now()
                )
                additional_triples.append(triple)
        
        # 分类关系抽取: X包括A、B、C
        category_pattern = r'(\w+)[包括|包含][：:]([^。]+)'
        category_matches = re.finditer(category_pattern, text)
        
        for match in category_matches:
            category = self._clean_entity(match.group(1))
            items_text = match.group(2)
            
            # 分割项目
            items = re.split(r'[、，,和与及]', items_text)
            
            for item in items:
                item = self._clean_entity(item.strip())
                
                if self._is_valid_entity(category) and self._is_valid_entity(item):
                    triple = KnowledgeTriple(
                        subject=item,
                        predicate="属于",
                        object=category,
                        confidence=0.7,
                        source=source,
                        timestamp=datetime.now()
                    )
                    additional_triples.append(triple)
        
        return additional_triples
    
    def _deduplicate_triples(self, triples: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """去重三元组"""
        seen_ids = set()
        unique_triples = []
        
        for triple in triples:
            triple_id = triple.get_id()
            if triple_id not in seen_ids:
                seen_ids.add(triple_id)
                unique_triples.append(triple)
        
        return unique_triples
    
    async def extract_from_file(self, file_path: str) -> List[KnowledgeTriple]:
        """从文件中抽取知识三元组"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 对于大文件，分段处理
            if len(text) > 10000:  # 10KB以上的文件分段处理
                chunks = self._split_text(text)
                all_triples = []
                for i, chunk in enumerate(chunks):
                    chunk_source = f"{file_path}#chunk_{i}"
                    chunk_triples = await self.extract_triples(chunk, chunk_source)
                    all_triples.extend(chunk_triples)
                return all_triples
            else:
                return await self.extract_triples(text, file_path)
                
        except Exception as e:
            logger.error(f"从文件抽取失败 {file_path}: {e}")
            return []
    
    def _split_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # 尝试在句号或换行符处分割
            if end < text_length:
                split_pos = text.rfind('。', start, end)
                if split_pos == -1:
                    split_pos = text.rfind('\n', start, end)
                if split_pos != -1:
                    end = split_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(end - overlap, start + 1)
        
        return chunks


# 创建模拟服务
async def create_mock_kg_service():
    """创建使用模拟抽取器的知识图谱服务"""
    from src.feynman.core.graph.service import KnowledgeGraphService
    from src.feynman.core.graph.storage import NetworkXStorage
    from src.feynman.core.graph.builder import KnowledgeGraphBuilder
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    
    # 替换为模拟抽取器
    kg_service.extractor = MockKnowledgeExtractor()
    
    return kg_service


if __name__ == "__main__":
    import asyncio
    
    async def test_mock_extractor():
        """测试模拟抽取器"""
        extractor = MockKnowledgeExtractor()
        
        test_text = """
        Python是一种编程语言，由Guido van Rossum在1991年发布。
        Python支持面向对象编程和函数式编程。
        机器学习包括监督学习、无监督学习和强化学习。
        """
        
        triples = await extractor.extract_triples(test_text, "test")
        
        print("🧪 模拟抽取器测试:")
        print(f"输入文本长度: {len(test_text)}")
        print(f"抽取三元组数: {len(triples)}")
        
        for i, triple in enumerate(triples, 1):
            print(f"{i}. {triple.subject} --[{triple.predicate}]--> {triple.object} (置信度: {triple.confidence})")
    
    asyncio.run(test_mock_extractor())
