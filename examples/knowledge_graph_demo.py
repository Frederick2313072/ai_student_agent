"""
知识图谱功能演示

展示如何使用知识图谱构建、查询和可视化功能。
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feynman.core.graph.service import KnowledgeGraphService
from src.feynman.core.graph.schema import KnowledgeGraphQuery


async def demo_knowledge_graph():
    """演示知识图谱功能"""
    print("🕸️ 知识图谱功能演示")
    print("=" * 50)
    
    # 初始化知识图谱服务
    kg_service = KnowledgeGraphService()
    
    # 示例文本
    sample_text = """
    Python是一种高级编程语言，由Guido van Rossum在1991年发布。
    Python支持多种编程范式，包括面向对象编程、函数式编程和过程式编程。
    Python被广泛应用于数据科学、人工智能、Web开发和自动化脚本。
    NumPy是Python的一个重要库，提供了数组计算功能。
    Pandas是基于NumPy的数据分析库，被数据科学家广泛使用。
    TensorFlow和PyTorch是Python中的深度学习框架。
    """
    
    print("📝 示例文本:")
    print(sample_text)
    print("\n" + "=" * 50)
    
    # 1. 从文本构建知识图谱
    print("🔨 正在从文本构建知识图谱...")
    build_result = await kg_service.build_from_text(sample_text, source="demo")
    
    if build_result["success"]:
        print(f"✅ 构建成功！")
        print(f"   - 添加三元组: {build_result.get('added_triples', 0)}")
        print(f"   - 总节点数: {build_result.get('graph_stats', {}).get('num_nodes', 0)}")
        print(f"   - 总边数: {build_result.get('graph_stats', {}).get('num_edges', 0)}")
    else:
        print(f"❌ 构建失败: {build_result.get('message', '未知错误')}")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 获取图统计信息
    print("📊 获取图统计信息...")
    stats = kg_service.get_stats()
    
    basic_stats = stats.get("basic", {})
    print(f"   - 节点总数: {basic_stats.get('num_nodes', 0)}")
    print(f"   - 边总数: {basic_stats.get('num_edges', 0)}")
    print(f"   - 平均度数: {basic_stats.get('avg_degree', 0)}")
    
    # 显示关系类型
    relationships = basic_stats.get("relationships", {})
    if relationships:
        print("   - 关系类型分布:")
        for rel_type, count in relationships.items():
            print(f"     * {rel_type}: {count}")
    
    # 显示重要实体
    top_entities = stats.get("top_entities", [])
    if top_entities:
        print("   - 重要实体排名:")
        for i, entity in enumerate(top_entities[:5], 1):
            print(f"     {i}. {entity['entity']} (度数: {entity['degree']})")
    
    print("\n" + "=" * 50)
    
    # 3. 搜索实体
    print("🔍 搜索实体...")
    search_results = kg_service.search_entities("Python", limit=5)
    
    if search_results:
        print("   搜索结果:")
        for entity in search_results:
            print(f"   - {entity['label']} (类型: {entity['type']}, 度数: {entity['degree']})")
    else:
        print("   未找到相关实体")
    
    print("\n" + "=" * 50)
    
    # 4. 获取子图
    if search_results:
        center_entity = search_results[0]['id']
        print(f"🌐 获取以'{center_entity}'为中心的子图...")
        
        query = KnowledgeGraphQuery(
            query_type="subgraph",
            center_node=center_entity,
            radius=1
        )
        
        subgraph = kg_service.query_graph(query)
        
        if subgraph.nodes:
            print(f"   子图包含 {len(subgraph.nodes)} 个节点，{len(subgraph.edges)} 条边")
            print("   节点:")
            for node in subgraph.nodes[:5]:
                print(f"   - {node.label}")
            
            print("   关系:")
            for edge in subgraph.edges[:5]:
                print(f"   - {edge.source} {edge.relationship} {edge.target}")
        else:
            print("   未找到子图数据")
    
    print("\n" + "=" * 50)
    
    # 5. 获取实体上下文
    if search_results:
        entity_id = search_results[0]['id']
        print(f"📋 获取实体'{entity_id}'的上下文...")
        
        context = kg_service.get_entity_context(entity_id, radius=1)
        
        if "error" not in context:
            related_triples = context.get("related_triples", [])
            print(f"   相关三元组数: {len(related_triples)}")
            
            if related_triples:
                print("   主要关系:")
                for triple in related_triples[:3]:
                    print(f"   - {triple['subject']} {triple['predicate']} {triple['object']}")
        else:
            print(f"   获取上下文失败: {context['error']}")
    
    print("\n" + "=" * 50)
    print("✨ 知识图谱演示完成！")
    
    # 6. 导出图数据
    print("\n💾 导出图数据...")
    exported_data = kg_service.export_graph(format="json")
    
    if exported_data:
        export_file = "data/demo_knowledge_graph.json"
        os.makedirs("data", exist_ok=True)
        
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(exported_data)
        
        print(f"   图数据已导出到: {export_file}")
    else:
        print("   导出失败")


def demo_api_endpoints():
    """演示API端点（需要启动服务）"""
    import requests
    
    api_base = "http://127.0.0.1:8005"
    
    print("\n🌐 API端点演示")
    print("=" * 50)
    
    try:
        # 测试构建API
        print("测试构建API...")
        response = requests.post(
            f"{api_base}/kg/build",
            json={"text": "机器学习是人工智能的一个分支。"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 构建API正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 构建API失败: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("⚠️ 服务未启动，跳过API测试")
        print("   请先运行: python run_app.py")
    
    except Exception as e:
        print(f"❌ API测试失败: {e}")


if __name__ == "__main__":
    print("启动知识图谱演示...")
    
    # 异步演示
    asyncio.run(demo_knowledge_graph())
    
    # API演示
    demo_api_endpoints()

