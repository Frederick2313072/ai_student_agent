"""
简单的知识图谱功能测试

使用模拟数据测试知识图谱的核心功能。
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feynman.core.graph.schema import KnowledgeTriple, GraphData
from src.feynman.core.graph.storage import NetworkXStorage
from src.feynman.core.graph.builder import KnowledgeGraphBuilder


def test_basic_functionality():
    """测试基础功能"""
    print("🧪 知识图谱基础功能测试")
    print("=" * 50)
    
    # 1. 创建存储后端
    storage = NetworkXStorage("data/test_knowledge_graph.json")
    builder = KnowledgeGraphBuilder(storage)
    
    # 2. 创建测试三元组
    test_triples = [
        KnowledgeTriple(subject="Python", predicate="是", object="编程语言", confidence=0.9),
        KnowledgeTriple(subject="Python", predicate="支持", object="面向对象编程", confidence=0.8),
        KnowledgeTriple(subject="Python", predicate="用于", object="数据科学", confidence=0.9),
        KnowledgeTriple(subject="NumPy", predicate="是", object="Python库", confidence=0.9),
        KnowledgeTriple(subject="NumPy", predicate="提供", object="数组计算", confidence=0.8),
        KnowledgeTriple(subject="Pandas", predicate="基于", object="NumPy", confidence=0.9),
        KnowledgeTriple(subject="数据科学", predicate="使用", object="Pandas", confidence=0.8)
    ]
    
    print(f"📝 创建了 {len(test_triples)} 个测试三元组")
    
    # 3. 构建知识图谱
    print("🔨 构建知识图谱...")
    build_result = builder.build_from_triples(test_triples)
    
    if build_result["success"]:
        print("✅ 构建成功！")
        print(f"   - 输入三元组: {build_result['input_triples']}")
        print(f"   - 处理后三元组: {build_result['processed_triples']}")
        print(f"   - 添加到图: {build_result['added_triples']}")
        
        stats = build_result["graph_stats"]
        print(f"   - 节点数: {stats.get('num_nodes', 0)}")
        print(f"   - 边数: {stats.get('num_edges', 0)}")
    else:
        print(f"❌ 构建失败: {build_result.get('error', '未知错误')}")
        return
    
    print("\n" + "=" * 50)
    
    # 4. 测试图查询
    print("🔍 测试图查询功能...")
    
    # 获取完整图
    full_graph = storage.get_graph()
    print(f"   完整图: {len(full_graph.nodes)} 个节点, {len(full_graph.edges)} 条边")
    
    # 获取子图
    subgraph = storage.get_subgraph("Python", radius=1)
    print(f"   Python子图: {len(subgraph.nodes)} 个节点, {len(subgraph.edges)} 条边")
    
    # 获取邻居
    neighbors = storage.get_neighbors("Python")
    print(f"   Python的邻居: {neighbors}")
    
    # 获取统计信息
    stats = storage.get_stats()
    print(f"   图统计: {stats}")
    
    print("\n" + "=" * 50)
    
    # 5. 测试图分析
    print("📊 测试图分析功能...")
    
    structure_analysis = builder.analyze_graph_structure()
    if "error" not in structure_analysis:
        node_analysis = structure_analysis.get("node_analysis", {})
        edge_analysis = structure_analysis.get("edge_analysis", {})
        
        print(f"   节点分析:")
        print(f"     - 平均度数: {node_analysis.get('avg_degree', 0):.2f}")
        print(f"     - 最大度数: {node_analysis.get('max_degree', 0)}")
        
        print(f"   边分析:")
        print(f"     - 关系类型: {list(edge_analysis.get('relationship_types', {}).keys())}")
        
        most_common = edge_analysis.get('most_common_relation')
        if most_common:
            print(f"     - 最常见关系: {most_common[0]} ({most_common[1]}次)")
    
    # 6. 测试实体重要性排名
    print("\n🏆 实体重要性排名:")
    importance_ranking = builder.get_entity_importance_ranking(top_k=5)
    
    for i, entity in enumerate(importance_ranking, 1):
        print(f"   {i}. {entity['entity']} (度数: {entity['degree']})")
    
    print("\n" + "=" * 50)
    print("✨ 基础功能测试完成！")
    
    # 7. 显示图的JSON表示
    print("\n📄 图数据示例:")
    graph_dict = full_graph.to_dict()
    
    print("   节点示例:")
    for node in graph_dict["nodes"][:3]:
        print(f"     - {node['label']} (ID: {node['id']})")
    
    print("   边示例:")
    for edge in graph_dict["edges"][:3]:
        print(f"     - {edge['source']} --[{edge['relationship']}]--> {edge['target']}")


if __name__ == "__main__":
    test_basic_functionality()

