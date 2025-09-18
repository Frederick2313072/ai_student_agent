"""
多Agent协作系统可视化
展示费曼学习系统的Agent架构、工作流程和数据流向
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mplfonts.bin.cli import init
import networkx as nx
import numpy as np
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import matplotlib.gridspec as gridspec

# 初始化中文字体支持
init()

# 设置中文字体
plt.rcParams['font.family'] = 'Source Han Sans CN'
plt.rcParams['axes.unicode_minus'] = False


def create_multi_agent_visualization():
    """创建多Agent系统的综合可视化"""
    
    # 创建大图画布
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('费曼学习系统 - 多Agent协作架构', fontsize=24, fontweight='bold', y=0.95)
    
    # 创建网格布局
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.2)
    
    # 1. 系统架构图 (左上，大块)
    ax1 = fig.add_subplot(gs[0:2, 0:2])
    draw_system_architecture(ax1)
    
    # 2. 工作流程图 (右上)
    ax2 = fig.add_subplot(gs[0, 2])
    draw_workflow_diagram(ax2)
    
    # 3. Agent能力矩阵 (右中)
    ax3 = fig.add_subplot(gs[1, 2])
    draw_agent_capabilities(ax3)
    
    # 4. 数据流向图 (底部)
    ax4 = fig.add_subplot(gs[2, :])
    draw_data_flow(ax4)
    
    plt.tight_layout()
    return fig


def draw_system_architecture(ax):
    """绘制系统架构图"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.set_title('多Agent系统架构', fontsize=16, fontweight='bold', pad=20)
    
    # 定义颜色方案
    colors = {
        'coordinator': '#FF6B6B',      # 协调层 - 红色
        'workflow': '#4ECDC4',         # 工作流层 - 青色
        'agents': '#45B7D1',           # Agent层 - 蓝色
        'infrastructure': '#FFA07A',    # 基础设施 - 橙色
        'user': '#98D8C8',             # 用户交互 - 浅绿
    }
    
    # 绘制层次结构
    
    # 1. 用户交互层
    user_box = FancyBboxPatch(
        (0.5, 8.5), 9, 1,
        boxstyle="round,pad=0.1",
        facecolor=colors['user'],
        edgecolor='black',
        linewidth=2
    )
    ax.add_patch(user_box)
    ax.text(5, 9, '用户交互层\n(Streamlit Web界面)', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 2. 工作流管理层
    workflow_box = FancyBboxPatch(
        (0.5, 7), 9, 1,
        boxstyle="round,pad=0.1",
        facecolor=colors['workflow'],
        edgecolor='black',
        linewidth=2
    )
    ax.add_patch(workflow_box)
    ax.text(5, 7.5, '多Agent工作流管理层\n(MultiAgentWorkflow - LangGraph)', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 3. 协调层
    coord_box = FancyBboxPatch(
        (2, 5.5), 6, 1,
        boxstyle="round,pad=0.1",
        facecolor=colors['coordinator'],
        edgecolor='black',
        linewidth=2
    )
    ax.add_patch(coord_box)
    ax.text(5, 6, '协调控制层\n(Coordinator Agent)', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 4. 专业Agent层
    agent_positions = [
        (0.5, 3.5, '解释分析器\nExplanationAnalyzer'),
        (2.5, 3.5, '知识验证器\nKnowledgeValidator'),
        (4.5, 3.5, '问题策略师\nQuestionStrategist'),
        (6.5, 3.5, '对话编排器\nConversationOrchestrator'),
        (8.5, 3.5, '洞察综合器\nInsightSynthesizer')
    ]
    
    for x, y, name in agent_positions:
        agent_box = FancyBboxPatch(
            (x-0.4, y-0.5), 1.8, 1,
            boxstyle="round,pad=0.05",
            facecolor=colors['agents'],
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(agent_box)
        ax.text(x+0.5, y, name, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 5. 基础设施层
    infra_positions = [
        (1.5, 1.5, '注册表\nAgentRegistry'),
        (4, 1.5, 'LLM引擎\n(OpenAI/智谱)'),
        (6.5, 1.5, '监控系统\nMonitoring'),
        (8.5, 1.5, '记忆存储\nMemory')
    ]
    
    for x, y, name in infra_positions:
        infra_box = FancyBboxPatch(
            (x-0.6, y-0.4), 1.2, 0.8,
            boxstyle="round,pad=0.05",
            facecolor=colors['infrastructure'],
            edgecolor='black',
            linewidth=1
        )
        ax.add_patch(infra_box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8)
    
    # 绘制连接线
    # 用户 -> 工作流
    ax.arrow(5, 8.4, 0, -0.3, head_width=0.1, head_length=0.05, fc='black', ec='black')
    
    # 工作流 -> 协调器
    ax.arrow(5, 6.9, 0, -0.3, head_width=0.1, head_length=0.05, fc='black', ec='black')
    
    # 协调器 -> Agents
    for x, y, _ in agent_positions:
        ax.arrow(5, 5.4, x+0.5-5, y+0.5-5.4, head_width=0.08, head_length=0.05, fc='gray', ec='gray', alpha=0.7)
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)


def draw_workflow_diagram(ax):
    """绘制工作流程图"""
    ax.set_title('LangGraph工作流程', fontsize=14, fontweight='bold')
    
    # 创建有向图
    G = nx.DiGraph()
    
    # 添加节点
    nodes = [
        ('start', '开始'),
        ('coord', '协调决策'),
        ('analysis', '解释分析'),
        ('validation', '知识验证'),
        ('questions', '问题生成'),
        ('orchestration', '对话编排'),
        ('synthesis', '洞察综合'),
        ('finalization', '最终化'),
        ('end', '结束')
    ]
    
    for node_id, label in nodes:
        G.add_node(node_id, label=label)
    
    # 添加边
    edges = [
        ('start', 'coord'),
        ('coord', 'analysis'),
        ('analysis', 'coord'),
        ('coord', 'validation'),
        ('validation', 'coord'),
        ('coord', 'questions'),
        ('questions', 'coord'),
        ('coord', 'orchestration'),
        ('orchestration', 'coord'),
        ('coord', 'synthesis'),
        ('synthesis', 'coord'),
        ('coord', 'finalization'),
        ('finalization', 'end')
    ]
    
    G.add_edges_from(edges)
    
    # 定义位置
    pos = {
        'start': (0.5, 1),
        'coord': (0.5, 0.8),
        'analysis': (0.1, 0.6),
        'validation': (0.3, 0.6),
        'questions': (0.7, 0.6),
        'orchestration': (0.9, 0.6),
        'synthesis': (0.5, 0.4),
        'finalization': (0.5, 0.2),
        'end': (0.5, 0)
    }
    
    # 绘制节点
    node_colors = ['#FFE5B4' if node == 'coord' else '#B4E5FF' for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, ax=ax)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=10, ax=ax)
    
    # 绘制标签
    labels = {node: data['label'] for node, data in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels, font_size=7, ax=ax)
    
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.1)
    ax.axis('off')


def draw_agent_capabilities(ax):
    """绘制Agent能力矩阵"""
    ax.set_title('Agent能力矩阵', fontsize=14, fontweight='bold')
    
    # 定义能力矩阵数据
    agents = ['解释分析器', '知识验证器', '问题策略师', '对话编排器', '洞察综合器']
    capabilities = ['文本理解', '事实验证', '策略规划', '流程控制', '知识综合']
    
    # 能力强度矩阵 (0-1)
    matrix = np.array([
        [0.9, 0.3, 0.2, 0.1, 0.4],  # 解释分析器
        [0.4, 0.9, 0.1, 0.2, 0.3],  # 知识验证器
        [0.3, 0.2, 0.9, 0.4, 0.1],  # 问题策略师
        [0.2, 0.1, 0.7, 0.9, 0.5],  # 对话编排器
        [0.5, 0.4, 0.3, 0.2, 0.9]   # 洞察综合器
    ])
    
    # 创建热力图
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    
    # 设置刻度和标签
    ax.set_xticks(range(len(capabilities)))
    ax.set_yticks(range(len(agents)))
    ax.set_xticklabels(capabilities, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(agents, fontsize=9)
    
    # 在每个格子中显示数值
    for i in range(len(agents)):
        for j in range(len(capabilities)):
            text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                         ha='center', va='center', color='white' if matrix[i, j] > 0.5 else 'black',
                         fontsize=8, fontweight='bold')
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label('能力强度', rotation=270, labelpad=15)


def draw_data_flow(ax):
    """绘制数据流向图"""
    ax.set_title('系统数据流向与协作关系', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    
    # 定义流程步骤
    steps = [
        (1, 2, '用户输入\n主题+解释', '#98D8C8'),
        (3, 3, '协调决策\n任务分派', '#FF6B6B'),
        (5, 3, '解释分析\n疑点识别', '#45B7D1'),
        (7, 3, '知识验证\n准确性检查', '#45B7D1'),
        (9, 3, '问题生成\n策略制定', '#45B7D1'),
        (11, 2, '最终输出\n问题+洞察', '#96CEB4')
    ]
    
    # 绘制流程步骤
    for x, y, text, color in steps:
        box = FancyBboxPatch(
            (x-0.6, y-0.4), 1.2, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # 绘制数据流箭头
    flow_arrows = [
        (1.6, 2, 2.4, 3, '解释文本'),
        (3.6, 3, 4.4, 3, '疑点列表'),
        (5.6, 3, 6.4, 3, '验证结果'),
        (7.6, 3, 8.4, 3, '策略选择'),
        (9.6, 3, 10.4, 2, '生成问题')
    ]
    
    for x1, y1, x2, y2, label in flow_arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', lw=2, color='darkblue'))
        # 添加数据标签
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2 + 0.3
        ax.text(mid_x, mid_y, label, ha='center', va='center', 
               fontsize=8, color='darkblue', fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # 添加反馈循环
    ax.annotate('', xy=(3, 2.6), xytext=(9, 2.6),
               arrowprops=dict(arrowstyle='->', lw=1.5, color='red', 
                             connectionstyle="arc3,rad=-0.3"))
    ax.text(6, 1.8, '协调反馈循环', ha='center', va='center', 
           fontsize=9, color='red', fontweight='bold')
    
    # 添加并行处理标识
    parallel_box = FancyBboxPatch(
        (4.5, 0.5), 4, 0.6,
        boxstyle="round,pad=0.05",
        facecolor='#FFE5B4',
        edgecolor='orange',
        linewidth=1.5,
        linestyle='--'
    )
    ax.add_patch(parallel_box)
    ax.text(6.5, 0.8, '并行处理区域\n(分析→验证→生成可同时进行)', 
           ha='center', va='center', fontsize=9, style='italic')
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)


def add_legend(fig):
    """添加图例说明"""
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor='#FF6B6B', label='协调控制层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#4ECDC4', label='工作流管理层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#45B7D1', label='专业Agent层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#FFA07A', label='基础设施层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#98D8C8', label='用户交互层')
    ]
    
    fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.92), fontsize=10)


if __name__ == "__main__":
    # 创建可视化
    fig = create_multi_agent_visualization()
    add_legend(fig)
    
    # 保存图片
    plt.savefig('/Users/frederick/Documents/ai_student_agent/multi_agent_system_visualization.png', 
                dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    
    # 显示图片
    plt.show()
    
    print("🎨 多Agent协作系统可视化图表已生成完成！")
    print("📊 图表包含了系统架构、工作流程、能力矩阵和数据流向四个维度的分析")
    print("💾 图片已保存至: multi_agent_system_visualization.png")
