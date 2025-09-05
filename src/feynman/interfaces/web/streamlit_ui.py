
import streamlit as st
import requests
import json
from typing import List, Dict, Generator

# 导入知识图谱UI组件
try:
    from .knowledge_graph_ui import kg_ui
except ImportError:
    # 处理直接运行时的导入问题
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from feynman.interfaces.web.knowledge_graph_ui import kg_ui

# --- 配置 ---
API_URL = "http://127.0.0.1:8000/api/v1/chat/stream"
st.set_page_config(page_title="🎓 AI学生费曼学习系统", layout="wide")


# --- 初始化会话状态 ---
def init_session_state():
    """初始化Streamlit的会话状态变量。"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "short_term_memory" not in st.session_state:
        st.session_state.short_term_memory = []
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = ""
    if "teaching_input" not in st.session_state:
        st.session_state.teaching_input = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "kg_enabled" not in st.session_state:
        st.session_state.kg_enabled = False
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "对话"


# --- API 调用函数 (V3.3: 流式改造) ---
def stream_chat_api(topic: str, explanation: str, session_id: str, memory: List[Dict]) -> Generator[str, None, None]:
    """调用后端的Agent流式聊天API。"""
    payload = {
        "topic": topic,
        "explanation": explanation,
        "session_id": session_id,
        "short_term_memory": memory
    }
    try:
        with requests.post(API_URL, json=payload, stream=True, timeout=300) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        try:

                            content_json = decoded_line[len('data: '):]
                            content = json.loads(content_json)
                            if content != "[END_OF_STREAM]":
                                yield content
                        except json.JSONDecodeError:
                            # 忽略无法解析的行
                            continue
    except requests.exceptions.RequestException as e:
        st.error(f"API请求失败: {e}")
        yield "" # 发生错误时，生成器也应终止

def call_memorize_api(topic: str, memory: List[Dict]):
    """调用后端的记忆API（即发即忘）。"""
    try:
        requests.post(
            "http://127.0.0.1:8000/api/v1/chat/memorize", 
            json={"topic": topic, "conversation_history": memory},
            timeout=5 # 设置一个短超时
        )
    except requests.exceptions.RequestException as e:
        # 这里可以选择性地在UI上显示一个不打扰的警告
        print(f"后台记忆请求失败: {e}")


# --- UI 渲染函数 ---
def render_chat_history():
    """渲染聊天历史记录。"""
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def render_main_ui():
    """渲染主界面。"""
    st.title("🎓 AI学生费曼学习系统")
    st.caption("一个基于LangGraph和费曼学习法的AI学生，通过提问帮你巩固知识。")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["💬 对话学习", "🕸️ 知识图谱"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_knowledge_graph_interface()


def render_chat_interface():
    """渲染对话界面"""

    with st.expander("ℹ️ 使用说明", expanded=False):
        st.markdown("""
        1.  **开始新会话**: 在侧边栏点击“开始新会话”按钮，这会清空所有学习记录。
        2.  **设定主题**: 在“当前学习主题”输入框中，输入你想要教授给AI学生的主题，例如“Python的GIL”。
        3.  **开始教授**: 在下方的文本框中，详细地向AI学生解释这个主题，然后点击“提交讲解”按钮。
        4.  **接收问题**: AI学生会分析你的解释，并提出一系列问题来检验你的理解。
        5.  **循环学习**: 你可以继续就它提出的问题或其他方面进行更详细的解释，实现教学相长的循环。
        """)

    with st.sidebar:
        st.header("⚙️ 会话控制")
        if st.button("开始新会话", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.short_term_memory = []
            st.session_state.current_topic = ""
            st.session_state.teaching_input = ""
            st.session_state.chat_history = []
            st.success("新会话已开始！")
            st.rerun()

        st.markdown("---")
        st.header("💡 当前状态")
        st.text_input("当前会话ID:", value=st.session_state.session_id, disabled=True)
        st.session_state.current_topic = st.text_input("当前学习主题:", value=st.session_state.current_topic)
        
        # 知识图谱侧边栏控制
        kg_enabled, viz_type, viz_options = kg_ui.render_sidebar_controls()
        st.session_state.kg_enabled = kg_enabled
        st.session_state.viz_options = viz_options if kg_enabled else {}
        
    render_chat_history()
    
    # 获取用户输入
    user_explanation = st.chat_input("请向我解释一下这个主题...")

    if user_explanation:
        if not st.session_state.current_topic:
            st.warning("在开始讲解前，请先在侧边栏设定一个学习主题。")
            return

        # 更新会话ID
        if not st.session_state.session_id:
            st.session_state.session_id = f"st-{st.session_state.current_topic.replace(' ', '_')}"

        # 显示用户消息
        st.session_state.chat_history.append({"role": "user", "content": user_explanation})
        with st.chat_message("user"):
            st.markdown(user_explanation)


        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            response_generator = stream_chat_api(
                st.session_state.current_topic,
                user_explanation,
                st.session_state.session_id,
                st.session_state.short_term_memory
            )
            for chunk in response_generator:
                full_response += chunk
                placeholder.markdown(full_response)
        
        # 将完整的流式响应添加到聊天历史和短期记忆中
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        st.session_state.short_term_memory.append({"role": "user", "content": user_explanation})
        st.session_state.short_term_memory.append({"role": "assistant", "content": full_response})
        

        call_memorize_api(st.session_state.current_topic, st.session_state.short_term_memory)
        
        # 如果启用了知识图谱，尝试从对话构建
        if st.session_state.get("kg_enabled", False):
            try:
                # 后台静默构建，不显示进度
                pass  # 暂时禁用自动构建，避免每次对话都触发
            except Exception as e:
                pass  # 静默处理错误


def render_knowledge_graph_interface():
    """渲染知识图谱界面"""
    if st.session_state.get("kg_enabled", False):
        viz_options = st.session_state.get("viz_options", {})
        viz_options["viz_type"] = st.selectbox(
            "选择可视化类型",
            ["网络图", "统计图表", "实体搜索"],
            key="kg_viz_type"
        )
        kg_ui.render_knowledge_graph_tab(viz_options)
    else:
        st.info("请在侧边栏启用知识图谱功能")
        
        # 显示功能说明
        with st.expander("🕸️ 知识图谱功能说明", expanded=True):
            st.markdown("""
            **知识图谱功能包括：**
            
            1. **自动构建**: 从对话内容、文本或文件自动抽取实体和关系
            2. **交互式可视化**: 使用Pyvis或Plotly展示知识网络
            3. **智能查询**: 支持实体搜索、子图查询、邻居分析
            4. **统计分析**: 提供节点度数分布、关系类型统计等
            5. **Agent集成**: AI学生可以利用知识图谱回答更有深度的问题
            
            **使用步骤：**
            1. 在侧边栏勾选"启用知识图谱可视化"
            2. 选择构建数据源（当前对话/文本/文件）
            3. 点击构建按钮生成知识图谱
            4. 在本页面查看和交互图谱可视化
            """)


if __name__ == "__main__":
    init_session_state()
    render_main_ui() 