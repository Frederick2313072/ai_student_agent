
import streamlit as st
import requests
import json
from typing import List, Dict, Generator

# --- 配置 ---
API_URL = "http://127.0.0.1:8000/chat/stream" # V3.3: 改为流式接口
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
                            # V3.4: 解析JSON编码的数据
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
            "http://127.0.0.1:8000/memorize", 
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

        # V3.4: 改造UI渲染逻辑以正确渲染Markdown流
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
        
        # V3.3: 异步调用记忆API
        call_memorize_api(st.session_state.current_topic, st.session_state.short_term_memory)


if __name__ == "__main__":
    init_session_state()
    render_main_ui() 