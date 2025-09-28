
import os
import argparse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredFileLoader

# --- 常量定义 ---
# 获取项目根目录的绝对路径 (该文件的上两级目录)
ABS_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 修正数据目录和数据库目录的路径
DATA_DIR = os.path.join(ABS_PATH, "data")
DB_DIR = os.path.join(ABS_PATH, "knowledge_base")
EMBEDDING_MODEL = "text-embedding-3-small"

def ingest_documents(file_name: str):
    """
    加载、处理单个文档并将其摄入到ChromaDB向量数据库中。
    使用UnstructuredFileLoader来支持多种文件格式。
    """
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在。")
        return

    print(f"--- 正在处理文件: {file_path} ---")

    # 1. 使用 UnstructuredFileLoader 加载文档
    # 这可以自动处理多种文件类型，如 .txt, .pdf, .docx 等
    try:
        loader = UnstructuredFileLoader(file_path)
        documents = loader.load()
        print(f"文档加载成功，共 {len(documents)} 个部分。")
    except Exception as e:
        print(f"使用 Unstructured 加载文件时出错: {e}")
        return

    # 2. 切分文本
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    print(f"文本切分成功，共 {len(splits)} 个块。")

    # 3. 向量化并存储
    print(f"--- 开始向量化并存入数据库 (目录: {DB_DIR}) ---")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    # 创建Chroma向量数据库实例，如果目录已存在，则会加载
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=DB_DIR
    )
    
    # 确保数据持久化到磁盘
    vectorstore.persist()
    
    print(f"--- 数据处理和存储成功！---")

if __name__ == "__main__":
    # --- 命令行参数解析 ---
    parser = argparse.ArgumentParser(description="文档处理和摄入脚本")
    parser.add_argument(
        "file", 
        type=str, 
        help="要处理的文档文件名，该文件必须位于 'data/' 目录下。"
    )
    args = parser.parse_args()

    # 检查OpenAI API Key是否存在
    # 为了方便，这里我们直接从 .env 加载
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("错误：请先在 .env 文件中设置 'OPENAI_API_KEY' 环境变量。")
    else:
        ingest_documents(args.file) 