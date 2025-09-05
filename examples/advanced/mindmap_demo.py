#!/usr/bin/env python3
"""
思维导图工具演示脚本
展示如何在费曼学习系统中使用思维导图和流程图工具
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def demo_mindmap_creation():
    """演示思维导图创建"""
    print("🧠 思维导图创建演示")
    print("=" * 50)
    
    # 模拟Agent使用思维导图工具的场景
    learning_topics = [
        {
            "topic": "深度学习基础",
            "content": """- 神经网络基础
  - 感知器
  - 多层感知器
  - 激活函数
- 深度网络架构
  - 卷积神经网络
    - 卷积层
    - 池化层
    - 全连接层
  - 循环神经网络
    - LSTM
    - GRU
- 训练技术
  - 反向传播
  - 梯度下降
  - 正则化
    - Dropout
    - Batch Normalization""",
            "style": "mermaid"
        },
        {
            "topic": "Python数据分析",
            "content": """- 数据处理库
  - NumPy
    - 数组操作
    - 数学函数
  - Pandas
    - DataFrame
    - 数据清洗
- 可视化库
  - Matplotlib
    - 基础图表
    - 自定义样式
  - Seaborn
    - 统计图表
    - 主题样式
- 机器学习库
  - Scikit-learn
    - 分类算法
    - 回归算法
    - 聚类算法""",
            "style": "plantuml"
        }
    ]
    
    for i, topic_data in enumerate(learning_topics, 1):
        print(f"\n📊 示例 {i}: {topic_data['topic']}")
        print("-" * 30)
        
        # 这里展示工具的预期输出
        print(f"使用 {topic_data['style']} 格式创建思维导图...")
        
        if topic_data['style'] == 'mermaid':
            demo_output = f"""思维导图已生成 - {topic_data['topic']}

Mermaid代码:
```mermaid
mindmap
  root)({topic_data['topic']})
    神经网络基础
      感知器
      多层感知器
      激活函数
    深度网络架构
      卷积神经网络
        卷积层
        池化层
        全连接层
      循环神经网络
        LSTM
        GRU
    训练技术
      反向传播
      梯度下降
      正则化
        Dropout
        Batch Normalization
```

在线查看: https://mermaid.live/edit#mindmap%0A%20%20root...
图片链接: https://mermaid.ink/img/mindmap%0A%20%20root...

你可以：
1. 复制Mermaid代码到支持的编辑器中
2. 点击在线链接直接查看和编辑
3. 使用图片链接在文档中引用
"""
        else:
            demo_output = f"""思维导图已生成 - {topic_data['topic']}

PlantUML代码:
```plantuml
@startmindmap
* {topic_data['topic']}
** 数据处理库
*** NumPy
**** 数组操作
**** 数学函数
*** Pandas
**** DataFrame
**** 数据清洗
** 可视化库
*** Matplotlib
**** 基础图表
**** 自定义样式
*** Seaborn
**** 统计图表
**** 主题样式
** 机器学习库
*** Scikit-learn
**** 分类算法
**** 回归算法
**** 聚类算法
@endmindmap
```

在线查看: http://www.plantuml.com/plantuml/uml/encoded_content
PNG图片: http://www.plantuml.com/plantuml/png/encoded_content
"""
        
        print(demo_output)

def demo_flowchart_creation():
    """演示流程图创建"""
    print("\n📈 流程图创建演示")
    print("=" * 50)
    
    process_examples = [
        {
            "title": "机器学习项目流程",
            "steps": """- 问题定义
- 数据收集
- 数据是否充足？
- 数据预处理
- 特征工程
- 模型选择
- 模型训练
- 模型评估
- 性能是否满意？
- 超参数调优
- 模型部署
- 监控和维护""",
            "style": "mermaid"
        },
        {
            "title": "科学研究方法",
            "steps": """- 提出假设
- 文献调研
- 设计实验
- 收集数据
- 数据分析
- 结果是否支持假设？
- 得出结论
- 撰写论文
- 同行评议""",
            "style": "plantuml"
        }
    ]
    
    for i, process in enumerate(process_examples, 1):
        print(f"\n🔄 示例 {i}: {process['title']}")
        print("-" * 30)
        
        print(f"使用 {process['style']} 格式创建流程图...")
        
        if process['style'] == 'mermaid':
            demo_output = f"""流程图已生成 - {process['title']}

Mermaid代码:
```mermaid
flowchart TD
    A1[问题定义]
    A2[数据收集]
    A3{{数据是否充足？}}
    A4[数据预处理]
    A5[特征工程]
    A6[模型选择]
    A7[模型训练]
    A8[模型评估]
    A9{{性能是否满意？}}
    A10[超参数调优]
    A11[模型部署]
    A12[监控和维护]
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A5 --> A6
    A6 --> A7
    A7 --> A8
    A8 --> A9
    A9 --> A10
    A10 --> A7
    A9 --> A11
    A11 --> A12
```

在线查看: https://mermaid.live/edit#flowchart%20TD...
图片链接: https://mermaid.ink/img/flowchart%20TD...
"""
        else:
            demo_output = f"""流程图已生成 - {process['title']}

PlantUML代码:
```plantuml
@startuml
title {process['title']}
start
:提出假设;
:文献调研;
:设计实验;
:收集数据;
:数据分析;
if (结果是否支持假设？) then (是)
  :得出结论;
else (否)
  :重新分析;
endif
:撰写论文;
:同行评议;
stop
@enduml
```

在线查看: http://www.plantuml.com/plantuml/uml/encoded_content
PNG图片: http://www.plantuml.com/plantuml/png/encoded_content
"""
        
        print(demo_output)

def demo_agent_integration():
    """演示Agent集成场景"""
    print("\n🤖 Agent集成场景演示")
    print("=" * 50)
    
    scenarios = [
        {
            "user_input": "用户解释机器学习的基本概念",
            "agent_analysis": "AI发现用户对监督学习和无监督学习的区别不够清楚",
            "mindmap_usage": "创建机器学习算法分类思维导图帮助理解"
        },
        {
            "user_input": "用户解释深度学习训练过程",
            "agent_analysis": "AI发现用户对训练流程的步骤顺序有疑问",
            "mindmap_usage": "创建深度学习训练流程图澄清步骤"
        },
        {
            "user_input": "用户解释Python数据结构",
            "agent_analysis": "AI发现用户需要系统化理解不同数据结构的特点",
            "mindmap_usage": "创建Python数据结构分类思维导图"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📝 场景 {i}:")
        print(f"用户输入: {scenario['user_input']}")
        print(f"AI分析: {scenario['agent_analysis']}")
        print(f"工具使用: {scenario['mindmap_usage']}")
        print(f"预期效果: 通过可视化帮助用户更好地理解概念结构")

def show_tool_capabilities():
    """展示工具能力总结"""
    print("\n🛠️ 思维导图工具能力总结")
    print("=" * 50)
    
    capabilities = {
        "支持的格式": [
            "📊 Mermaid思维导图 - 现代化界面",
            "📊 Mermaid流程图 - 流程可视化", 
            "🎯 PlantUML思维导图 - 专业外观",
            "🎯 PlantUML流程图 - 丰富图表",
            "📈 QuickChart网络图 - 复杂关系(可选)"
        ],
        "在线服务": [
            "🌐 Mermaid Live Editor - 在线编辑",
            "📱 Mermaid Image Service - 图片生成",
            "🖥️ PlantUML Server - 在线渲染",
            "☁️ QuickChart API - 图表服务"
        ],
        "核心特性": [
            "⚡ 完全使用外部API，无本地依赖",
            "🔄 智能语法转换",
            "🌍 多层级结构支持",
            "🔗 自动生成分享链接",
            "📸 一键导出图片",
            "🛡️ 完善的错误处理"
        ],
        "学习场景": [
            "📚 概念结构梳理",
            "🧠 知识体系构建",
            "📋 学习计划制定", 
            "🔍 问题分析分解",
            "📈 流程步骤说明",
            "🎯 重点难点标记"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  {item}")

def main():
    """主演示函数"""
    print("🎨 AI学生Agent思维导图工具演示")
    print("=" * 60)
    print("展示新增的可视化工具如何增强费曼学习体验")
    print("=" * 60)
    
    # 运行各个演示
    demo_mindmap_creation()
    demo_flowchart_creation()
    demo_agent_integration()
    show_tool_capabilities()
    
    # 总结
    print("\n" + "=" * 60)
    print("🎉 演示完成")
    print("=" * 60)
    
    print("\n💡 关键优势:")
    print("  ✅ 纯API调用，无需本地安装图形库")
    print("  ✅ 多种格式支持，满足不同需求")
    print("  ✅ 在线编辑，便于分享和协作")
    print("  ✅ 与费曼学习理念完美结合")
    
    print("\n🚀 使用方法:")
    print("  1. 在Agent中调用 create_mindmap() 创建思维导图")
    print("  2. 在Agent中调用 create_flowchart() 创建流程图")
    print("  3. 复制生成的代码到支持的编辑器")
    print("  4. 点击在线链接直接查看和编辑")
    print("  5. 使用图片链接在文档中引用")
    
    print("\n📖 完整文档: docs/tools_guide.md")
    print("🧪 运行测试: python3 simple_mindmap_test.py")

if __name__ == "__main__":
    main()
