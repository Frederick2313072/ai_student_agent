
import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import ZhipuAIEmbeddings

# 常量定义
ABS_PATH = os.path.dirname(os.path.abspath(__file__)) 
MEMORY_DB_DIR = os.path.join(ABS_PATH, "..", "..", "long_term_memory")


class LongTermMemoryManager:
    """
    负责管理Agent的长期记忆。
    
    使用ChromaDB作为向量存储，用于持久化和检索对话摘要。
    """
    def __init__(self):
        """初始化长期记忆管理器，并根据环境变量动态选择嵌入模型。"""


        zhipu_api_key = os.getenv("ZHIPU_API_KEY", "").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

        if zhipu_api_key:
            # 使用智谱AI的嵌入模型
            self._embeddings = ZhipuAIEmbeddings(
                api_key=zhipu_api_key,
                model=os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-2") # 默认使用 embedding-2
            )
        elif openai_api_key:
            # 使用OpenAI的嵌入模型
            base_url = os.getenv("OPENAI_BASE_URL", "").strip()
            model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            if base_url:
                self._embeddings = OpenAIEmbeddings(model=model_name, base_url=base_url)
            else:
                self._embeddings = OpenAIEmbeddings(model=model_name)
        else:

            self._embeddings = None
            self._vectorstore = None
            return
            
        self._vectorstore = Chroma(
            persist_directory=MEMORY_DB_DIR,
            embedding_function=self._embeddings
        )

    def add_memory(self, summary: str, metadata: dict = None):
        """
        将一段文本（通常是对话摘要）作为新的记忆存入数据库。

        Args:
            summary (str): 要存入的记忆文本。
            metadata (dict, optional): 与此记忆相关的元数据。
        """
        if not self._vectorstore:

            return
            

        self._vectorstore.add_texts(texts=[summary], metadatas=[metadata] if metadata else None)
        # ChromaDB的某些模式需要手动持久化
        self._vectorstore.persist()


# 创建一个全局实例，以便在应用中方便地调用
memory_manager_instance = LongTermMemoryManager()

def add_new_memory(summary: str, metadata: dict = None):
    """
    一个便捷的函数，用于调用全局实例来添加新记忆。
    """
    memory_manager_instance.add_memory(summary, metadata) 