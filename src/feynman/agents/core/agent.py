
import os
import json
import time
from typing import List, Dict, Any, TypedDict, Annotated
from operator import add
import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# 导入模块
from feynman.agents.tools import ALL_TOOLS
from feynman.agents.prompts.prompt_manager import prompt_manager, get_prompt
from feynman.infrastructure.database.memory.memory import add_new_memory

# 监控模块（可选）
try:
    from feynman.infrastructure.monitoring.tracing.otlp import (
        trace_langchain_workflow, trace_conversation_flow, trace_memory_operation,
        add_span_attribute, add_span_event, initialize_tracing, trace_span
    )
    from feynman.infrastructure.monitoring.tracing.langfuse import (
        initialize_langfuse, create_conversation_tracker, track_conversation_quality
    )
    from feynman.infrastructure.monitoring.metrics.prometheus import (
        monitor_workflow_node, record_conversation_start, record_conversation_end,
        record_llm_usage
    )
    from feynman.infrastructure.monitoring.logging.structured import get_logger, set_request_context, log_workflow_execution
    from feynman.infrastructure.monitoring.cost.tracker import get_cost_tracker
    MONITORING_AVAILABLE = True
except ImportError as e:
    # 监控模块不可用，使用兼容模式
    def trace_langchain_workflow(name): return lambda f: f
    def trace_conversation_flow(*args): return lambda f: f
    def trace_memory_operation(name): return lambda f: f
    def monitor_workflow_node(name): return lambda f: f
    def add_span_attribute(*args): pass
    def add_span_event(*args): pass
    def initialize_tracing(): pass
    def initialize_langfuse(): return False
    def get_logger(name): 
        import logging
        return logging.getLogger(name)
    def set_request_context(*args): pass
    def log_workflow_execution(*args): pass
    def get_cost_tracker(): return None
    def trace_span(*args): 
        from contextlib import nullcontext
        return nullcontext()
    MONITORING_AVAILABLE = False

# 监控系统初始化
logger = get_logger("agent.core")

# 初始化追踪系统（如果可用）
if MONITORING_AVAILABLE:
    initialize_tracing()
    initialize_langfuse()
    logger.info("监控系统已初始化")
else:
    logger.warning("监控系统不可用，使用兼容模式")

# 模型初始化
# LangSmith：仅当存在 API Key 时才默认打开，否则强制关闭，避免未授权报错
langsmith_key = os.getenv("LANGCHAIN_API_KEY", "").strip()
if langsmith_key:
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")


def initialize_model():
    """根据环境变量初始化并返回相应的LLM和模型提供商。"""
    
    zhipu_api_key = os.getenv("ZHIPU_API_KEY", "").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if zhipu_api_key:
        model = ChatZhipuAI(
            api_key=zhipu_api_key,
            model=os.getenv("ZHIPU_MODEL", "glm-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
        )
        return model, "zhipu"
    
    if openai_api_key:
        print("未检测到智谱AI配置，使用OpenAI。")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        model_kwargs = {
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        }
        if openai_base_url:
            model_kwargs["base_url"] = openai_base_url
        
        model = ChatOpenAI(**model_kwargs)
        return model, "openai"

    return None, None

# 条件初始化模型
try:
    model, model_provider = initialize_model()
    MODEL_AVAILABLE = model is not None
except Exception as e:
    model, model_provider = None, None
    MODEL_AVAILABLE = False


# Agent状态定义
class AgentState(TypedDict):
    topic: str
    user_explanation: str
    unclear_points: List[str]
    question_queue: List[str]
    short_term_memory: List[Dict]
    messages: Annotated[List[BaseMessage], add]
    _analysis_result: Dict


# Agent工具和模型
tools = ALL_TOOLS
# 如果是智谱AI，则禁用部分搜索工具
if model_provider == "zhipu":
    from feynman.agents.tools.tools import web_search, search_academic_papers, search_wikipedia
    
    # 移除联网搜索工具
    disabled_tools = {web_search.name, search_academic_papers.name, search_wikipedia.name}
    tools = [tool for tool in ALL_TOOLS if tool.name not in disabled_tools]
    

if MODEL_AVAILABLE and model:
    react_agent_executor = create_react_agent(model, tools=tools)
else:
    react_agent_executor = None


# LangGraph节点定义

@monitor_workflow_node("user_input_handler")
@trace_langchain_workflow("user_input_handler")
def user_input_handler(state: AgentState) -> AgentState:
    """接收用户输入，准备Agent的初始状态，并更新短期记忆。"""

    topic = state.get("topic", "")
    user_explanation = state.get("user_explanation", "")
    
    # 添加追踪属性
    add_span_attribute("workflow.node", "user_input_handler")
    add_span_attribute("conversation.topic", topic)
    add_span_attribute("input.explanation_length", len(user_explanation))
    
    # 更新短期记忆
    short_term_memory = state.get("short_term_memory", [])
    short_term_memory.append({"role": "user", "content": user_explanation})
    
    prompt_text = get_prompt("user_analysis_prompt", topic=topic, user_explanation=user_explanation)
    
    add_span_event("prompt_generated", {
        "prompt_length": len(prompt_text),
        "memory_count": len(short_term_memory)
    })
    
    return {
        "messages": [HumanMessage(content=prompt_text)],
        "short_term_memory": short_term_memory,
        "topic": topic,
        "user_explanation": user_explanation,
    }


@monitor_workflow_node("gap_identifier_react")
@trace_langchain_workflow("gap_identifier_react")
def gap_identifier_react(state: AgentState) -> AgentState:
    """运行ReAct Agent来识别知识缺口，使用稳定的结构化输出解析。"""

    
    topic = state.get("topic", "")
    start_time = time.time()
    
    # 添加追踪属性
    add_span_attribute("workflow.node", "gap_identifier_react")
    add_span_attribute("conversation.topic", topic)
    add_span_attribute("input.messages_count", len(state.get("messages", [])))
    
    try:
        # 检查ReAct Agent是否可用
        if not react_agent_executor:
            print("⚠️  ReAct Agent不可用，使用模拟输出")
            
            # 模拟分析结果
            mock_result = {
                "unclear_points": ["模拟疑点：概念理解需要进一步澄清"],
                "_analysis_result": {
                    "unclear_points": [{"content": "模拟疑点：概念理解需要进一步澄清", "severity": "medium"}],
                    "is_complete": False,
                    "summary": "由于系统处于测试模式，这是一个模拟的分析结果"
                }
            }
            return mock_result
        
        # 仅将 messages 传入 ReAct 执行器
        with trace_span("react_agent_execution") as span:
            agent_output = react_agent_executor.invoke({"messages": state.get("messages", [])})
            span.set_attribute("agent.output_messages", len(agent_output.get("messages", [])))
        
        final_answer = agent_output['messages'][-1].content

        
        # 使用新的稳定解析器
        from feynman.agents.parsers import AgentOutputParser
        
        # 解析输出
        with trace_span("output_parsing") as span:
            analysis_result = AgentOutputParser.parse_agent_output(final_answer)
            span.set_attribute("parsing.unclear_points_count", len(analysis_result.unclear_points))
            span.set_attribute("parsing.is_complete", analysis_result.is_complete)
            span.set_attribute("parsing.summary_length", len(analysis_result.summary))
        

        
        # 转换为原有格式以保持向后兼容
        if analysis_result.is_complete and not analysis_result.unclear_points:
            unclear_points = []
        else:
            unclear_points = [point.content for point in analysis_result.unclear_points]
        
        # 记录成功事件
        duration_ms = (time.time() - start_time) * 1000
        add_span_event("analysis_completed", {
            "unclear_points_count": len(unclear_points),
            "is_complete": analysis_result.is_complete,
            "duration_ms": duration_ms
        })
        
        # 记录工作流执行日志
        log_workflow_execution(
            node_name="gap_identifier_react",
            success=True,
            duration_ms=duration_ms,
            input_topic=topic,
            output_questions_count=len(unclear_points)
        )
            
        return {
            "unclear_points": unclear_points,
            # 保存完整解析结果用于高级功能
            "_analysis_result": analysis_result.dict()
        }
        
    except Exception as e:

        
        # 记录错误事件
        duration_ms = (time.time() - start_time) * 1000
        add_span_event("analysis_failed", {
            "error": str(e),
            "error_type": type(e).__name__,
            "duration_ms": duration_ms
        })
        
        # 记录错误日志
        log_workflow_execution(
            node_name="gap_identifier_react",
            success=False,
            duration_ms=duration_ms,
            input_topic=topic,
            error=str(e)
        )
        
        # 降级处理：返回通用疑点
        return {
            "unclear_points": ["处理用户解释时出现技术问题，请重新解释或换个表达方式"],
            "_analysis_result": {
                "unclear_points": [],
                "is_complete": False,
                "summary": f"解析错误: {str(e)}"
            }
        }


@monitor_workflow_node("question_generator")
@trace_langchain_workflow("question_generator")
def question_generator(state: AgentState) -> AgentState:
    """根据识别出的疑点，生成问题并更新短期记忆。"""

    
    topic = state.get("topic", "")
    unclear_points = state.get("unclear_points", [])
    start_time = time.time()
    
    # 添加追踪属性
    add_span_attribute("workflow.node", "question_generator")
    add_span_attribute("conversation.topic", topic)
    add_span_attribute("input.unclear_points_count", len(unclear_points))
    
    if not unclear_points:
        question = "我对您的解释完全理解了，没有更多问题了！"
        
        add_span_event("conversation_completed", {
            "completion_type": "no_unclear_points",
            "final_question": question
        })
        
        # 记录对话完成
        duration_ms = (time.time() - start_time) * 1000
        log_workflow_execution(
            node_name="question_generator",
            success=True,
            duration_ms=duration_ms,
            input_topic=topic,
            output_questions_count=1
        )
        
        return {
            "question_queue": [question],
            "short_term_memory": state.get("short_term_memory", []) + [{"role": "assistant", "content": question}]
        }

    questions = []
    for point in unclear_points:
        question_template = prompt_manager.get_template("agent", "question_templates")["unclear_point_question"]
        questions.append(question_template.format(point=point))
    
    # 将生成的问题也加入短期记忆
    updated_memory = state.get("short_term_memory", [])
    for q in questions:
        updated_memory.append({"role": "assistant", "content": q})
    
    # 记录问题生成事件
    duration_ms = (time.time() - start_time) * 1000
    add_span_event("questions_generated", {
        "questions_count": len(questions),
        "unclear_points_count": len(unclear_points),
        "duration_ms": duration_ms
    })
    
    log_workflow_execution(
        node_name="question_generator",
        success=True,
        duration_ms=duration_ms,
        input_topic=topic,
        output_questions_count=len(questions)
    )
        
    return {"question_queue": questions, "short_term_memory": updated_memory}


# 后台记忆固化

@trace_memory_operation("summarize_and_store")
def summarize_conversation_for_memory(topic: str, conversation_history: List[Dict]):
    """
    (后台任务) 对话结束后，对短期记忆进行总结，并固化到长期记忆中。
    """

    
    start_time = time.time()
    cost_tracker = get_cost_tracker()
    
    # 添加追踪属性
    add_span_attribute("memory.operation", "summarize_and_store")
    add_span_attribute("memory.topic", topic)
    add_span_attribute("memory.conversation_length", len(conversation_history))
    
    summary_prompt = prompt_manager.get_template("agent", "memory_summary_prompt")
    
    summarization_chain = summary_prompt | model
    
    conversation_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    if not conversation_str.strip():

        add_span_event("memory_skipped", {"reason": "empty_conversation"})
        return

    with trace_span("llm_summarization") as span:
        if not MODEL_AVAILABLE or not model:
            print("⚠️  模型不可用，使用简化摘要")
            summary = f"主题: {topic}\n对话轮数: {len(conversation_history)}\n时间: {datetime.datetime.now().isoformat()}"
            llm_duration = 0.001
        else:
            llm_start_time = time.time()
            summary = summarization_chain.invoke({"conversation_str": conversation_str}).content
            llm_duration = time.time() - llm_start_time
        
        span.set_attribute("llm.duration_ms", llm_duration * 1000)
        span.set_attribute("llm.input_length", len(conversation_str))
        span.set_attribute("llm.output_length", len(summary))
        
        # 记录LLM使用
        estimated_prompt_tokens = len(conversation_str) // 4
        estimated_completion_tokens = len(summary) // 4
        
        model_name = getattr(model, 'model_name', getattr(model, 'model', 'unknown'))
        cost_record = cost_tracker.record_usage(
            model=model_name,
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens,
            request_type="summarization"
        )
    

    
    # 定义元数据
    metadata = {
        "topic": topic,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # 将摘要存入长期记忆
    with trace_span("memory_storage") as span:
        add_new_memory(summary, metadata)
        span.set_attribute("memory.summary_length", len(summary))
    
    # 记录成功事件
    total_duration_ms = (time.time() - start_time) * 1000
    add_span_event("memory_stored", {
        "summary_length": len(summary),
        "total_duration_ms": total_duration_ms
    })
    
    # 记录操作成功


# 构建LangGraph工作流

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
 