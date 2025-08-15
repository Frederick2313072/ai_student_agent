
import os
import json
from typing import List, Dict, Any, TypedDict, Annotated
from operator import add
import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI # 新增导入
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 从新模块中导入
from .tools import knowledge_retriever, memory_retriever, file_operation, web_search, image_search
from .prompts import react_prompt
from core.memory import add_new_memory

# --- 环境和模型初始化 --- (V3.2: 环境变量加载移至 main.py)
# LangSmith：仅当存在 API Key 时才默认打开，否则强制关闭，避免未授权报错
langsmith_key = os.getenv("LANGCHAIN_API_KEY", "").strip()
if langsmith_key:
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")

# --- 模型初始化 ---
def initialize_model():
    """根据环境变量初始化并返回相应的LLM。"""
    
    zhipu_api_key = os.getenv("ZHIPU_API_KEY", "").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if zhipu_api_key:
        print("检测到智谱AI配置，优先使用智谱AI。")
        return ChatZhipuAI(
            api_key=zhipu_api_key,
            model=os.getenv("ZHIPU_MODEL", "glm-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
        )
    
    if openai_api_key:
        print("未检测到智谱AI配置，使用OpenAI。")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        model_kwargs = {
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        }
        if openai_base_url:
            model_kwargs["base_url"] = openai_base_url
        
        return ChatOpenAI(**model_kwargs)

    raise ValueError("错误：请在.env文件中设置 ZHIPU_API_KEY 或 OPENAI_API_KEY")

model = initialize_model()


# 确保关键API密钥已设置
# if not os.getenv("OPENAI_API_KEY"):
#     raise ValueError("错误：请在.env文件中设置OPENAI_API_KEY")
if not os.getenv("TAVILY_API_KEY"):
    print("警告：TAVILY_API_KEY未设置，web_search工具将无法工作。")

# 允许通过 OPENAI_BASE_URL 指定 OpenAI 兼容端点（如代理/Azure/OpenRouter兼容端点）
# openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
# if openai_base_url:
#     model = ChatOpenAI(temperature=0, model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), base_url=openai_base_url)
# else:
#     model = ChatOpenAI(temperature=0, model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"))

# --- Agent状态定义 (V3.1) ---
class AgentState(TypedDict):
    topic: str
    user_explanation: str
    unclear_points: List[str]
    question_queue: List[str]
    short_term_memory: List[Dict] # 短期记忆：最近K轮对话
    messages: Annotated[List[BaseMessage], add]


# --- 构建ReAct Agent ---
tools = [knowledge_retriever, memory_retriever, file_operation, web_search, image_search]
# 使用默认的ReAct提示词，避免自定义Prompt变量不匹配导致的启动错误
react_agent_executor = create_react_agent(model, tools=tools)


# --- LangGraph 节点定义 ---

def user_input_handler(state: AgentState) -> AgentState:
    """接收用户输入，准备Agent的初始状态，并更新短期记忆。"""
    print("--- 节点: user_input_handler ---")
    topic = state.get("topic", "")
    user_explanation = state.get("user_explanation", "")
    
    # 更新短期记忆
    short_term_memory = state.get("short_term_memory", [])
    short_term_memory.append({"role": "user", "content": user_explanation})
    
    prompt_text = (
        f"这是用户（老师）对主题“{topic}”的解释，请你深入分析，找出所有疑点: "
        f"\n\n---\n\n{user_explanation}"
    )
    
    return {
        "messages": [HumanMessage(content=prompt_text)],
        "short_term_memory": short_term_memory,
        "topic": topic,
        "user_explanation": user_explanation,
    }


def gap_identifier_react(state: AgentState) -> AgentState:
    """运行ReAct Agent来识别知识缺口。"""
    print("--- 节点: gap_identifier (ReAct) ---")
    # 仅将 messages 传入 ReAct 执行器
    agent_output = react_agent_executor.invoke({"messages": state.get("messages", [])})
    final_answer = agent_output['messages'][-1].content
    print(f"--- ReAct Agent Final Answer: {final_answer} ---")
    
    try:
        unclear_points = json.loads(final_answer)
    except (json.JSONDecodeError, TypeError):
        unclear_points = [final_answer]

    return {"unclear_points": unclear_points}


def question_generator(state: AgentState) -> AgentState:
    """根据识别出的疑点，生成问题并更新短期记忆。"""
    print("--- 节点: question_generator ---")
    unclear_points = state.get("unclear_points", [])
    if not unclear_points:
        question = "我对您的解释完全理解了，没有更多问题了！"
        return {
            "question_queue": [question],
            "short_term_memory": state.get("short_term_memory", []) + [{"role": "assistant", "content": question}]
        }

    questions = []
    for point in unclear_points:
        questions.append(f"关于您提到的“{point}”，我不太理解，能再详细解释一下吗？")
    
    # 将生成的问题也加入短期记忆
    updated_memory = state.get("short_term_memory", [])
    for q in questions:
        updated_memory.append({"role": "assistant", "content": q})
        
    return {"question_queue": questions, "short_term_memory": updated_memory}


# --- V3.2: 后台记忆固化 ---

def summarize_conversation_for_memory(topic: str, conversation_history: List[Dict]):
    """
    (后台任务) 对话结束后，对短期记忆进行总结，并固化到长期记忆中。
    """
    print("--- 后台任务: memory_manager ---")
    
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "你的任务是为以下对话生成一个简洁、信息丰富的摘要，以作为未来可以检索的记忆。"
         "请提炼出核心概念、关键问答和最终结论。摘要应以第三人称视角编写。"),
        ("human", "请为这段对话创建摘要:\n{conversation_str}")
    ])
    
    summarization_chain = summary_prompt | model
    
    conversation_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    if not conversation_str.strip():
        print("--- 短期记忆为空，跳过记忆固化。 ---")
        return

    summary = summarization_chain.invoke({"conversation_str": conversation_str}).content
    
    print(f"--- 生成的记忆摘要: {summary} ---")
    
    # 定义元数据
    metadata = {
        "topic": topic,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # 将摘要存入长期记忆
    add_new_memory(summary, metadata)


# --- 构建LangGraph图 (V3.2) ---

def build_graph():
    workflow = StateGraph(AgentState)  # type: ignore[arg-type]

    workflow.add_node("user_input_handler", user_input_handler)
    workflow.add_node("gap_identifier", gap_identifier_react)
    workflow.add_node("question_generator", question_generator)

    workflow.set_entry_point("user_input_handler")
    workflow.add_edge("user_input_handler", "gap_identifier")
    workflow.add_edge("gap_identifier", "question_generator")
    workflow.add_edge("question_generator", END) # 在此结束主流程

    app = workflow.compile()
    return app

# # 如果直接运行此文件，可以用于测试
# if __name__ == '__main__':
#     graph_app = build_graph()
    
#     # 模拟一次完整的调用
#     inputs = {
#         "topic": "Python的GIL",
#         "user_explanation": "GIL是Python的一个全局锁，它保证了任何时候只有一个线程在执行。这意味着Python的多线程并不能利用多核CPU来并行计算，只适合IO密集型任务。"
#     }
    
#     # 流式输出每个节点的执行结果
#     for event in graph_app.stream(inputs, stream_mode="values"):
#         print("\n--- New Event ---")
#         print(event) 