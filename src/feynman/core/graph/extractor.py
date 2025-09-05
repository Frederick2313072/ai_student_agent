"""
知识图谱实体关系抽取器

支持基于LLM的实体关系抽取，并提供spaCy作为备选方案。
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os

# 移除spacy依赖，只使用LLM抽取

from .schema import KnowledgeTriple

logger = logging.getLogger(__name__)


class KnowledgeExtractor:
    """知识抽取器"""
    
    def __init__(self):
        """初始化抽取器"""
        self.llm = self._init_llm()
        self.extraction_prompt = self._create_extraction_prompt()
    
    def _init_llm(self):
        """初始化LLM模型"""
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        zhipu_api_key = os.getenv("ZHIPU_API_KEY", "").strip()
        
        # 从环境变量获取超时配置
        llm_timeout = int(os.getenv("LLM_TIMEOUT", "120"))
        
        # 优先使用OpenAI
        if openai_api_key:
            try:
                return ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),  # 使用更快的模型
                    temperature=0.1,
                    api_key=openai_api_key,
                    timeout=llm_timeout,
                    max_retries=1  # 减少重试次数以加快失败检测
                )
            except Exception as e:
                logger.warning(f"OpenAI初始化失败: {e}")
        
        # 备选智谱AI
        if zhipu_api_key:
            try:
                return ChatZhipuAI(
                    api_key=zhipu_api_key,
                    model=os.getenv("ZHIPU_MODEL", "glm-4"),
                    temperature=0.1,
                    timeout=llm_timeout,
                    max_retries=1
                )
            except Exception as e:
                logger.warning(f"智谱AI初始化失败: {e}")
        
        logger.warning("所有LLM API均不可用，将使用规则抽取器")
        return None
    

    
    def _create_extraction_prompt(self):
        """创建实体关系抽取的提示词"""
        prompt = ChatPromptTemplate.from_template("""
你是一个专业的知识图谱构建助手。请从以下文本中抽取结构化知识，返回三元组列表。

**抽取规则：**
1. 识别重要的实体（人名、概念、技术术语、方法等）
2. 识别实体间的关系（是什么、属于、使用、导致、包含等）
3. 保持抽取的准确性，避免推测
4. 对于复杂句子，可拆分为多个简单三元组
5. 关系动词要规范化（如：包含、属于、导致、实现、使用等）

**输出格式：**
请返回JSON格式，包含triples数组，每个三元组有subject、predicate、object、confidence字段。

文本内容：
{text}

请返回JSON格式的抽取结果：
""")
        return prompt
    
    async def extract_triples_llm(self, text: str, source: Optional[str] = None) -> List[KnowledgeTriple]:
        """使用LLM抽取知识三元组"""
        if not self.llm:
            logger.warning("LLM未配置，跳过LLM抽取")
            return []
        
        try:
            # 构建提示词
            messages = self.extraction_prompt.format_messages(text=text)
            
            # 调用LLM
            if hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(messages)
            else:
                # 对于不支持异步的模型，使用同步调用
                response = self.llm.invoke(messages)
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 解析JSON响应
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                else:
                    logger.error("LLM响应中未找到有效JSON")
                    return []
                
                # 转换为KnowledgeTriple对象
                triples = []
                for triple_data in result_data.get("triples", []):
                    triple = KnowledgeTriple(
                        subject=triple_data["subject"],
                        predicate=triple_data["predicate"],
                        object=triple_data["object"],
                        confidence=triple_data.get("confidence", 0.8),
                        source=source
                    )
                    triples.append(triple)
                
                logger.info(f"LLM抽取到 {len(triples)} 个三元组")
                return triples
                
            except json.JSONDecodeError as e:
                logger.error(f"解析LLM响应JSON失败: {e}")
                return []
                
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"LLM抽取失败 ({error_type}): {error_msg}")
            
            # 更详细的错误分类
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.warning("LLM API调用超时，建议检查网络连接或增加超时时间")
            elif "rate limit" in error_msg.lower():
                logger.warning("LLM API速率限制，请稍后重试")
            elif "api key" in error_msg.lower():
                logger.warning("LLM API密钥问题，请检查配置")
            elif "余额不足" in error_msg or "balance" in error_msg.lower():
                logger.warning("LLM API余额不足，请充值或检查配置")
            elif "1113" in error_msg:  # 智谱AI余额不足错误码
                logger.warning("智谱AI余额不足，建议使用OpenAI或充值")
            
            return []
    

    
    def extract_triples_rule_based(self, text: str, source: Optional[str] = None) -> List[KnowledgeTriple]:
        """基于规则的简单知识抽取（备用方案）"""
        triples = []
        sentences = text.split('。')
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
                
            # 简单规则：查找关系词
            patterns = [
                (r'(.{1,20})是(.{1,20})的(.{1,20})', lambda m: (m.group(3), "是", m.group(1))),
                (r'(.{1,20})属于(.{1,20})', lambda m: (m.group(1), "属于", m.group(2))),
                (r'(.{1,20})包含(.{1,20})', lambda m: (m.group(1), "包含", m.group(2))),
                (r'(.{1,20})用于(.{1,20})', lambda m: (m.group(1), "用于", m.group(2))),
            ]
            
            for pattern, extractor in patterns:
                import re
                match = re.search(pattern, sentence)
                if match:
                    try:
                        subject, predicate, obj = extractor(match)
                        subject = subject.strip()[:15]
                        obj = obj.strip()[:15]
                        
                        if len(subject) > 1 and len(obj) > 1 and subject != obj:
                            triple = KnowledgeTriple(
                                subject=subject,
                                predicate=predicate,
                                object=obj,
                                confidence=0.6,
                                source=source
                            )
                            triples.append(triple)
                    except Exception:
                        continue
                        
        logger.info(f"规则抽取器生成 {len(triples)} 个三元组")
        return triples[:8]  # 限制数量

    async def extract_triples(self, text: str, source: Optional[str] = None) -> List[KnowledgeTriple]:
        """
        综合抽取知识三元组：优先LLM，备用规则抽取
        """
        all_triples = []
        
        # 1. 尝试LLM抽取
        if self.llm:
            llm_triples = await self.extract_triples_llm(text, source)
            all_triples.extend(llm_triples)
            logger.info(f"LLM抽取得到 {len(llm_triples)} 个三元组")
        
        # 2. 如果LLM抽取失败，使用规则抽取器
        if len(all_triples) == 0:
            logger.warning("LLM抽取失败，启用规则抽取器")
            rule_triples = self.extract_triples_rule_based(text, source)
            all_triples.extend(rule_triples)
        
        # 3. 去重和过滤
        return self._deduplicate_triples(all_triples)
    
    def _deduplicate_triples(self, triples: List[KnowledgeTriple]) -> List[KnowledgeTriple]:
        """去重三元组"""
        seen_ids = set()
        unique_triples = []
        
        for triple in triples:
            triple_id = triple.get_id()
            if triple_id not in seen_ids:
                seen_ids.add(triple_id)
                unique_triples.append(triple)
        
        logger.info(f"去重后保留 {len(unique_triples)} 个唯一三元组")
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
