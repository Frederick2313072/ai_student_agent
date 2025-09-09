"""
知识图谱可视化界面

基于Streamlit的知识图谱交互式可视化组件。
"""

import streamlit as st
import requests
import json
import logging
from typing import Dict, Any, List, Optional
import tempfile
import os
from datetime import datetime
import pandas as pd

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

# 已删除Pyvis和Plotly导入，仅保留Graphviz作为可视化引擎

logger = logging.getLogger(__name__)


class KnowledgeGraphUI:
    """知识图谱UI组件"""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base_url = api_base_url
        self.kg_api_url = f"{api_base_url}/api/v1/kg"
        
    def render_sidebar_controls(self):
        """渲染侧边栏控制组件"""
        st.sidebar.markdown("---")
        st.sidebar.header("🕸️ 知识图谱")
        
        # 图谱显示开关
        kg_enabled = st.sidebar.checkbox("启用知识图谱可视化", value=False)
        
        if kg_enabled:
            # 可视化选项
            viz_type = st.sidebar.selectbox(
                "可视化类型",
                ["网络图", "统计图表", "实体搜索"]
            )
            
            # 过滤选项
            with st.sidebar.expander("过滤选项", expanded=True):
                topic_filter = st.text_input("主题过滤", "")
                node_limit = st.number_input("节点数限制", min_value=10, max_value=1000, value=100)
                
                if viz_type == "网络图":
                    layout_type = st.selectbox("布局类型", ["力导向", "层次", "圆形"])
                    node_size_metric = st.selectbox("节点大小", ["度数", "均匀"])
                
            # 构建选项
            with st.sidebar.expander("构建知识图谱", expanded=False):
                build_source = st.selectbox("数据源", ["当前对话", "上传文件", "文本输入"])
                
                if build_source == "文本输入":
                    build_text = st.text_area("输入文本", height=100)
                    if st.button("从文本构建", width='stretch'):
                        if build_text.strip():
                            self._build_from_text(build_text)
                
                elif build_source == "当前对话":
                    if st.button("从当前对话构建", width='stretch'):
                        self._build_from_conversation()
                
                elif build_source == "上传文件":
                    uploaded_file = st.file_uploader("选择文件", type=['txt', 'md', 'pdf'])
                    if uploaded_file and st.button("从文件构建", width='stretch'):
                        self._build_from_file(uploaded_file)
            
            return kg_enabled, viz_type, {
                "topic_filter": topic_filter,
                "node_limit": node_limit,
                "layout_type": layout_type if viz_type == "网络图" else None,
                "node_size_metric": node_size_metric if viz_type == "网络图" else None
            }
        
        return False, None, {}
    
    def render_knowledge_graph_tab(self, viz_options: Dict[str, Any]):
        """渲染知识图谱主界面"""
        st.header("🕸️ 知识图谱可视化")
        
        viz_type = viz_options.get("viz_type", "网络图")
        
        if viz_type == "网络图":
            self._render_network_graph(viz_options)
        elif viz_type == "统计图表":
            self._render_statistics_charts()
        elif viz_type == "实体搜索":
            self._render_entity_search()
    
    def _render_network_graph(self, options: Dict[str, Any]):
        """渲染网络图"""
        try:
            # 获取图数据
            graph_data = self._fetch_graph_data(
                topic_filter=options.get("topic_filter"),
                limit=options.get("node_limit", 100)
            )
            
            if not graph_data:
                st.warning("暂无知识图谱数据")
                return
            
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            if not nodes:
                st.info("当前过滤条件下无可显示的节点")
                return
            
            st.subheader(f"网络图 ({len(nodes)} 个节点, {len(edges)} 条边)")
            
            # 使用Graphviz可视化引擎
            if not GRAPHVIZ_AVAILABLE:
                st.error("缺少Graphviz依赖包，请安装: `uv add graphviz` 和 `brew install graphviz`")
                return
            
            # 直接使用Graphviz渲染
            self._render_graphviz_graph(nodes, edges, options)
            
            # 显示图统计
            self._render_graph_stats(graph_data)
            
        except Exception as e:
            st.error(f"渲染网络图失败: {e}")
            logger.error(f"网络图渲染错误: {e}")
    
    def _render_graphviz_graph(self, nodes: List[Dict], edges: List[Dict], options: Dict[str, Any]):
        """使用Graphviz渲染有向图"""
        try:
            # 创建Graphviz有向图
            dot = graphviz.Digraph(comment='知识图谱')
            dot.attr('graph', rankdir='TB', size='12,8', dpi='300')
            dot.attr('node', shape='ellipse', style='filled', fontname='SimHei')
            dot.attr('edge', fontname='SimHei')
            
            # 添加节点
            for node in nodes:
                node_id = str(node["id"])
                node_label = str(node["label"]).strip()
                node_type = node.get('type', 'entity')
                degree = node.get('degree', 0)
                
                # 根据节点类型和度数设置颜色
                if node_type == 'technology':
                    color = 'lightblue'
                elif node_type == 'algorithm':
                    color = 'lightgreen'
                elif node_type == 'application':
                    color = 'lightyellow'
                else:
                    color = 'lightgray'
                    
                # 根据度数调整节点大小（通过字体大小）
                fontsize = str(max(10, min(20, 10 + degree * 2)))
                
                dot.node(
                    node_id, 
                    label=node_label,
                    fillcolor=color,
                    fontsize=fontsize,
                    tooltip=f"类型: {node_type}\\n度数: {degree}"
                )
            
            # 添加边
            for edge in edges:
                source_id = str(edge["source"])
                target_id = str(edge["target"])
                relationship = str(edge["relationship"]).strip()
                weight = edge.get("weight", 1.0)
                
                # 根据权重调整边的粗细
                penwidth = str(max(1.0, min(5.0, weight * 3)))
                
                dot.edge(
                    source_id, 
                    target_id, 
                    label=relationship,
                    penwidth=penwidth,
                    tooltip=f"关系: {relationship}\\n权重: {weight:.2f}"
                )
            
            # 选择输出格式
            col1, col2 = st.columns(2)
            with col1:
                output_format = st.selectbox(
                    "输出格式", 
                    ["SVG", "PNG", "PDF"],
                    help="选择图形输出格式"
                )
            
            with col2:
                graph_layout = st.selectbox(
                    "图布局方向", 
                    [("从上到下", "TB"), ("从左到右", "LR"), ("从下到上", "BT"), ("从右到左", "RL")],
                    format_func=lambda x: x[0],
                    help="选择图形布局方向"
                )
            
            # 设置布局方向
            dot.attr('graph', rankdir=graph_layout[1])
            
            # 渲染图形
            if output_format == "SVG":
                svg_data = dot.pipe(format='svg', encoding='utf-8')
                st.image(svg_data, width='stretch')
            elif output_format == "PNG":
                png_data = dot.pipe(format='png')
                st.image(png_data, width='stretch')
            elif output_format == "PDF":
                pdf_data = dot.pipe(format='pdf')
                st.download_button(
                    label="下载PDF文件",
                    data=pdf_data,
                    file_name="knowledge_graph.pdf",
                    mime="application/pdf"
                )
                # 同时显示SVG预览
                svg_data = dot.pipe(format='svg', encoding='utf-8')
                st.image(svg_data, width='stretch')
            
            # 显示DOT源码
            with st.expander("查看Graphviz DOT源码"):
                st.code(dot.source, language='dot')
                st.download_button(
                    label="下载DOT文件",
                    data=dot.source,
                    file_name="knowledge_graph.dot",
                    mime="text/plain"
                )
            
        except Exception as e:
            st.error(f"Graphviz渲染失败: {e}")
            logger.error(f"Graphviz渲染错误: {e}")
            # 提供troubleshooting信息
            st.info("💡 如果出现渲染错误，请确保系统已安装Graphviz软件：\n- macOS: `brew install graphviz`\n- Ubuntu: `sudo apt-get install graphviz`\n- Windows: 从 https://graphviz.org/download/ 下载安装")

    def _render_statistics_charts(self):
        """渲染统计图表"""
        try:
            stats = self._fetch_graph_stats()
            
            if not stats:
                st.warning("暂无统计数据")
                return
            
            st.subheader("📊 知识图谱统计")
            
            # 基础统计
            basic_stats = stats.get("basic", {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("节点总数", basic_stats.get("num_nodes", 0))
            with col2:
                st.metric("边总数", basic_stats.get("num_edges", 0))
            with col3:
                st.metric("平均度数", f"{basic_stats.get('avg_degree', 0):.2f}")
            
            # 关系类型分布
            relationships = basic_stats.get("relationships", {})
            if relationships:
                st.subheader("关系类型分布")
                
                # 使用Streamlit原生条形图
                rel_df = pd.DataFrame({
                    '关系类型': list(relationships.keys()),
                    '数量': list(relationships.values())
                })
                st.bar_chart(rel_df.set_index('关系类型'))
            
            # 重要实体排名
            top_entities = stats.get("top_entities", [])
            if top_entities:
                st.subheader("重要实体排名（按度数）")
                
                # 使用Streamlit表格和条形图
                entity_df = pd.DataFrame(top_entities[:10])
                entity_df.index = entity_df.index + 1
                st.dataframe(entity_df)
                
                # 简单条形图
                chart_df = entity_df.set_index('entity')['degree']
                st.bar_chart(chart_df)
            
        except Exception as e:
            st.error(f"渲染统计图表失败: {e}")
            logger.error(f"统计图表渲染错误: {e}")
    
    def _render_entity_search(self):
        """渲染实体搜索功能"""
        st.subheader("🔍 实体搜索")
        
        search_query = st.text_input("搜索实体", placeholder="输入实体名称或关键词...")
        
        if search_query:
            try:
                # 搜索实体
                search_results = self._search_entities(search_query)
                
                if search_results:
                    st.success(f"找到 {len(search_results)} 个相关实体")
                    
                    # 显示搜索结果
                    for entity in search_results:
                        with st.expander(f"🔸 {entity['label']} (度数: {entity['degree']})"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**ID**: {entity['id']}")
                                st.write(f"**类型**: {entity['type']}")
                                st.write(f"**匹配分数**: {entity.get('score', 0):.2f}")
                            
                            with col2:
                                if st.button(f"查看子图", key=f"subgraph_{entity['id']}"):
                                    self._show_entity_subgraph(entity['id'])
                                
                                if st.button(f"查看上下文", key=f"context_{entity['id']}"):
                                    self._show_entity_context(entity['id'])
                else:
                    st.info(f"未找到与'{search_query}'相关的实体")
                    
            except Exception as e:
                st.error(f"搜索失败: {e}")
                logger.error(f"实体搜索错误: {e}")
    
    def _show_entity_subgraph(self, entity_id: str):
        """显示实体子图"""
        try:
            subgraph_data = self._fetch_subgraph(entity_id, radius=2)
            
            if subgraph_data and subgraph_data.get("nodes"):
                st.subheader(f"实体 '{entity_id}' 的子图")
                
                # 使用简化的实体列表显示
                nodes = subgraph_data["nodes"]
                edges = subgraph_data["edges"]
                
                # 创建NetworkX图用于布局
                if NETWORKX_AVAILABLE:
                    G = nx.Graph()
                    for node in nodes:
                        G.add_node(node["id"], **node)
                    for edge in edges:
                        G.add_edge(edge["source"], edge["target"])
                    
                    pos = nx.spring_layout(G)
                else:
                    st.error("NetworkX未安装，无法计算图布局")
                    return
                
                # 绘制子图（使用Graphviz）
                st.info("🎯 子图可视化功能已简化，请使用主图查看相关实体")
                
                # 显示相关实体列表
                st.write(f"**实体 '{entity_id}' 的相关实体:**")
                related_entities = set()
                for edge in edges:
                    if edge["source"] == entity_id:
                        related_entities.add(edge["target"])
                    elif edge["target"] == entity_id:
                        related_entities.add(edge["source"])
                
                for entity in sorted(related_entities):
                    st.write(f"• {entity}")
                    
                if not related_entities:
                    st.write("暂无相关实体")
            else:
                st.warning(f"实体 '{entity_id}' 没有相关的子图数据")
                
        except Exception as e:
            st.error(f"显示子图失败: {e}")
    
    def _show_entity_context(self, entity_id: str):
        """显示实体上下文"""
        try:
            response = requests.get(
                f"{self.kg_api_url}/entity/{entity_id}/context",
                params={"radius": 1},
                timeout=10
            )
            
            if response.status_code == 200:
                context_data = response.json()["data"]
                
                st.subheader(f"实体 '{entity_id}' 的上下文")
                
                # 相关三元组
                triples = context_data.get("related_triples", [])
                if triples:
                    st.write("**相关关系:**")
                    for triple in triples[:10]:
                        confidence_text = f" (置信度: {triple.get('confidence', 0):.2f})" if triple.get('confidence') else ""
                        st.write(f"- {triple['subject']} **{triple['predicate']}** {triple['object']}{confidence_text}")
                
                # 邻居统计
                neighbors_count = context_data.get("neighbors_count", 0)
                st.write(f"**邻居节点数**: {neighbors_count}")
                
            else:
                st.error(f"获取上下文失败: {response.text}")
                
        except Exception as e:
            st.error(f"显示上下文失败: {e}")
    
    def _render_graph_stats(self, graph_data: Dict[str, Any]):
        """渲染图统计信息"""
        metadata = graph_data.get("metadata", {})
        
        if metadata:
            with st.expander("📈 图统计信息", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**总节点数**: {metadata.get('total_nodes', 0)}")
                    st.write(f"**总边数**: {metadata.get('total_edges', 0)}")
                
                with col2:
                    if metadata.get("filtered"):
                        st.write("**状态**: 已过滤")
                    else:
                        st.write("**状态**: 完整图谱")
    
    def _build_from_text(self, text: str):
        """从文本构建知识图谱"""
        with st.spinner("正在从文本构建知识图谱..."):
            try:
                response = requests.post(
                    f"{self.kg_api_url}/build",
                    json={"text": text},
                    timeout=180  # 增加到3分钟，给LLM足够的处理时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"构建成功！{result.get('message', '')}")
                    
                    data = result.get("data", {})
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("新增三元组", data.get("triples_added", 0))
                    with col2:
                        st.metric("总节点数", data.get("total_nodes", 0))
                    with col3:
                        st.metric("总边数", data.get("total_edges", 0))
                        
                    st.rerun()
                else:
                    st.error(f"构建失败: {response.text}")
                    
            except Exception as e:
                st.error(f"构建过程中出错: {e}")
    
    def _build_from_conversation(self):
        """从当前对话构建知识图谱"""
        if "chat_history" not in st.session_state or not st.session_state.chat_history:
            st.warning("当前没有对话历史可用于构建知识图谱")
            return
        
        with st.spinner("正在从对话历史构建知识图谱..."):
            try:
                conversation_history = st.session_state.chat_history
                
                response = requests.post(
                    f"{self.kg_api_url}/build/conversation",
                    json={"conversation_history": conversation_history},
                    timeout=180  # 增加到3分钟，给LLM足够的处理时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"从对话构建成功！{result.get('message', '')}")
                    st.rerun()
                else:
                    st.error(f"从对话构建失败: {response.text}")
                    
            except Exception as e:
                st.error(f"从对话构建过程中出错: {e}")
    
    def _build_from_file(self, uploaded_file):
        """从上传文件构建知识图谱"""
        # 暂存文件
        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner(f"正在从文件 {uploaded_file.name} 构建知识图谱..."):
                response = requests.post(
                    f"{self.kg_api_url}/build",
                    json={"file_path": temp_path},
                    timeout=180  # 增加到3分钟，与其他构建请求保持一致
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"从文件构建成功！{result.get('message', '')}")
                    st.rerun()
                else:
                    st.error(f"从文件构建失败: {response.text}")
        
        except Exception as e:
            st.error(f"文件处理失败: {e}")
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _fetch_graph_data(self, topic_filter: Optional[str] = None, limit: int = 100) -> Optional[Dict[str, Any]]:
        """获取图数据"""
        try:
            params = {"limit": limit}
            if topic_filter and topic_filter.strip():
                params["topic"] = topic_filter.strip()
            
            response = requests.get(f"{self.kg_api_url}/graph", params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                logger.error(f"获取图数据失败: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"获取图数据错误: {e}")
            return None
    
    def _fetch_subgraph(self, center_node: str, radius: int = 1) -> Optional[Dict[str, Any]]:
        """获取子图数据"""
        try:
            params = {"center": center_node, "radius": radius}
            response = requests.get(f"{self.kg_api_url}/subgraph", params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                logger.error(f"获取子图失败: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"获取子图错误: {e}")
            return None
    
    def _fetch_graph_stats(self) -> Optional[Dict[str, Any]]:
        """获取图统计数据"""
        try:
            response = requests.get(f"{self.kg_api_url}/stats", timeout=30)
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                logger.error(f"获取统计数据失败: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"获取统计数据错误: {e}")
            return None
    
    def _search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索实体"""
        try:
            params = {"query": query, "limit": limit}
            response = requests.get(f"{self.kg_api_url}/search", params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()["data"]["entities"]
            else:
                logger.error(f"搜索实体失败: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"搜索实体错误: {e}")
            return []
    
    def _calculate_node_size(self, node: Dict[str, Any], metric: str) -> int:
        """计算节点显示大小"""
        if metric == "度数":
            degree = node.get("degree", 0)
            return max(10, min(50, degree * 3 + 15))
        else:  # 均匀
            return 20
    
    def _get_node_color(self, node: Dict[str, Any]) -> str:
        """获取节点颜色"""
        node_type = node.get("type", "entity")
        color_map = {
            "entity": "#97C2FC",
            "concept": "#FB7E81", 
            "person": "#7BE141",
            "event": "#FFA807",
            "location": "#AD85E4"
        }
        return color_map.get(node_type, "#97C2FC")


# 全局实例
kg_ui = KnowledgeGraphUI()
