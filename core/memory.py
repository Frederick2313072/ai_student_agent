
import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# --- 常量定义 ---
# 获取当前文件所在目录的绝对路径
ABS_PATH = os.path.dirname(os.path.abspath(__file__)) 
# 定义长期记忆数据库的持久化存储目录
MEMORY_DB_DIR = os.path.join(ABS_PATH, "..", "..", "long_term_memory")
# 定义嵌入模型
EMBEDDING_MODEL = "text-embedding-3-small"


class LongTermMemoryManager:
    """
    负责管理Agent的长期记忆。
    
    使用ChromaDB作为向量存储，用于持久化和检索对话摘要。
    """
    def __init__(self):
        """初始化长期记忆管理器。"""
        print(f"--- 初始化长期记忆数据库于: {MEMORY_DB_DIR} ---")
        self._embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
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
        print(f"--- 正在向长期记忆中添加新条目... ---")
        self._vectorstore.add_texts(texts=[summary], metadatas=[metadata] if metadata else None)
        # ChromaDB的某些模式需要手动持久化
        self._vectorstore.persist()
        print(f"--- 新记忆已成功存入并持久化。---")

# 创建一个全局实例，以便在应用中方便地调用
memory_manager_instance = LongTermMemoryManager()

def add_new_memory(summary: str, metadata: dict = None):
    """
    一个便捷的函数，用于调用全局实例来添加新记忆。
    """
    memory_manager_instance.add_memory(summary, metadata) 